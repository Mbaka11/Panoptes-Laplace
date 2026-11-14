import CoreLocation
import Foundation
import Observation

// LOC-01 (Location), foreground only, when-in-use only. docs/sensor-probe-spec.md sections 3, 4, 8.
// TEST BUILD, not cleared for real data (gate R): samples are kept IN MEMORY ONLY, are lost when
// the app exits, and there is no export, network or transfer code. Coordinates are never logged
// or printed and are not displayed.

/// Authorization as reported by the OS (spec 3.1), kept separate from the probe's own state.
enum OSAuthorization: String, Sendable {
    case notDetermined = "not_determined"
    case restricted
    case denied
    case authorizedWhenInUse = "authorized (when in use)"
    case authorizedAlways = "authorized (always)"
    case unknown

    var isAuthorized: Bool { self == .authorizedWhenInUse || self == .authorizedAlways }

    init(_ s: CLAuthorizationStatus) {
        switch s {
        case .notDetermined: self = .notDetermined
        case .restricted: self = .restricted
        case .denied: self = .denied
        case .authorizedWhenInUse: self = .authorizedWhenInUse
        case .authorizedAlways: self = .authorizedAlways
        @unknown default: self = .unknown
        }
    }
}

enum OSAccuracy: String, Sendable {
    case full, reduced, unknown
    init(_ a: CLAccuracyAuthorization) {
        switch a {
        case .fullAccuracy: self = .full
        case .reducedAccuracy: self = .reduced
        @unknown default: self = .unknown
        }
    }
}

/// One control event (CTL-01). Never contains sample values or coordinates.
struct ControlEvent: Identifiable {
    let id = UUID()
    let time: Date
    let source: String
    let action: String          // explained, declined_preprompt, os_prompt_requested, enabled, paused, resumed, authorization_change_observed, revocation_observed, deleted_all
    let probeBefore: ProbeState
    let probeAfter: ProbeState
    let osState: String         // "auth / accuracy" as observed at that moment
    let actor: String           // participant | probe_inferred
}

/// A location sample. Device-local, in memory only.
struct LocationSample {
    let eventTime: Date          // source time (CLLocation.timestamp)
    let receiveTime: Date
    let latitude: Double
    let longitude: Double
    let horizontalAccuracy: Double
    let speed: Double?           // nil when the OS reports it invalid (negative)
    let course: Double?          // nil when invalid
    let method: String           // sampling method, predeclared
    let delivery: String         // live
    let simulatedBySoftware: Bool?
    let producedByAccessory: Bool?
    let segment: Int             // continuous collection run (increments on start/resume/foreground return)
}

@MainActor
@Observable
final class LocationModule: NSObject, CLLocationManagerDelegate {
    static let sourceId = "LOC-01"
    /// Predeclared sampling parameters (spec 4.1: recorded, not hidden).
    static let method = "standard_updates_foreground"
    static let desiredAccuracyLabel = "nearest_ten_meters"
    static let minIntervalSeconds: TimeInterval = 5
    static let gapThresholdSeconds: TimeInterval = 30

    private(set) var probeState: ProbeState = .off
    private(set) var os: OSAuthorization = .unknown
    private(set) var accuracy: OSAccuracy = .unknown
    private(set) var osObservedAt: Date?
    private(set) var samples: [LocationSample] = []
    private(set) var controlLog: [ControlEvent] = []
    private(set) var discardedInvalid = 0
    private(set) var pausedIntervals: [(from: Date, to: Date?)] = []
    private(set) var isUpdating = false

    @ObservationIgnored private let manager = CLLocationManager()
    @ObservationIgnored private var lastAccepted: Date?
    @ObservationIgnored private var segment = 0
    @ObservationIgnored private var appActive = false
    @ObservationIgnored private var awaitingOSPrompt = false
    @ObservationIgnored private var lastSeenAuth: OSAuthorization?
    @ObservationIgnored private var lastSeenAccuracy: OSAccuracy?

    override init() {
        super.init()
        manager.delegate = self
        manager.desiredAccuracy = kCLLocationAccuracyNearestTenMeters
        manager.distanceFilter = kCLDistanceFilterNone
        manager.activityType = .other
        manager.pausesLocationUpdatesAutomatically = false
        // allowsBackgroundLocationUpdates stays false: no background mode is declared (later step).
        refreshOSState(reason: nil)
    }

    // MARK: derived

    var isCollecting: Bool { probeState == .on && os.isAuthorized && appActive && isUpdating }
    var osLabel: String { os.rawValue + (os.isAuthorized ? ", accuracy: \(accuracy.rawValue)" : "") }

    var firstSample: Date? { samples.first?.eventTime }
    var latestSample: Date? { samples.last?.eventTime }

    /// Gaps over the threshold between consecutive samples of the same continuous run. Gaps are
    /// reported as gaps, never as stillness (spec 4.4).
    var gapStats: (count: Int, longest: TimeInterval) {
        var n = 0; var longest: TimeInterval = 0
        for (a, b) in zip(samples, samples.dropFirst()) where a.segment == b.segment {
            let d = b.eventTime.timeIntervalSince(a.eventTime)
            if d > Self.gapThresholdSeconds { n += 1; longest = max(longest, d) }
        }
        return (n, longest)
    }
    var segmentCount: Int { Set(samples.map(\.segment)).count }

    // MARK: participant actions

    func logExplained() { log("explained", before: probeState, after: probeState, actor: "participant") }

    func declinePrePrompt() {
        log("declined_preprompt", before: probeState, after: probeState, actor: "participant")
        // Source stays as it was (off); no OS dialog is triggered.
    }

    /// Called only after the participant chose "Continuer vers la demande du système".
    func enableAfterPrePrompt() {
        let before = probeState
        refreshOSState(reason: nil)
        probeState = .on
        log("enabled", before: before, after: .on, actor: "participant")
        switch os {
        case .notDetermined:
            awaitingOSPrompt = true
            log("os_prompt_requested", before: .on, after: .on, actor: "probe_inferred")
            manager.requestWhenInUseAuthorization()
        case .authorizedWhenInUse, .authorizedAlways:
            startIfPossible()
        case .denied, .restricted, .unknown:
            probeState = .blockedByOS   // no repeated prompting (spec 3.2)
        }
    }

    func pause() {
        guard probeState == .on else { return }
        stopUpdates()
        pausedIntervals.append((Date(), nil))
        probeState = .paused
        log("paused", before: .on, after: .paused, actor: "participant")
    }

    /// Resume starts from now. Location has no OS-held history, so there is nothing to backfill.
    func resume() {
        guard probeState == .paused else { return }
        refreshOSState(reason: nil)
        closePausedInterval()
        probeState = .on
        log("resumed", before: .paused, after: .on, actor: "participant")
        if os.isAuthorized { startIfPossible() } else { probeState = .blockedByOS }
    }

    /// Deletes every in-memory sample for this source. The control log is kept (it holds no
    /// coordinates) and is cleared only when the app exits.
    func deleteAllSamples() {
        let n = samples.count
        samples.removeAll(keepingCapacity: false)
        discardedInvalid = 0
        segment = 0
        lastAccepted = nil
        log("deleted_all", before: probeState, after: probeState, actor: "participant", note: "\(n) samples")
    }

    // MARK: lifecycle

    func appDidBecomeActive() {
        appActive = true
        refreshOSState(reason: "foreground")
        if probeState == .on { startIfPossible() }
    }

    func appDidLeaveForeground() {
        appActive = false
        // No background mode: stop explicitly so the gap is ours and visible, not an OS surprise.
        stopUpdates()
    }

    // MARK: internals

    private func startIfPossible() {
        guard probeState == .on, os.isAuthorized, appActive, !isUpdating else { return }
        segment += 1
        lastAccepted = nil
        isUpdating = true
        manager.startUpdatingLocation()
    }

    private func stopUpdates() {
        guard isUpdating else { return }
        manager.stopUpdatingLocation()
        isUpdating = false
    }

    private func closePausedInterval() {
        if let i = pausedIntervals.indices.last, pausedIntervals[i].to == nil {
            pausedIntervals[i].to = Date()
        }
    }

    /// Reads the OS state now and reacts to any change (revocation, scope change).
    private func refreshOSState(reason: String?) {
        apply(auth: OSAuthorization(manager.authorizationStatus),
              accuracy: OSAccuracy(manager.accuracyAuthorization))
    }

    private func apply(auth newAuth: OSAuthorization, accuracy newAcc: OSAccuracy) {
        let prevAuth = lastSeenAuth, prevAcc = lastSeenAccuracy
        os = newAuth; accuracy = newAcc; osObservedAt = Date()
        lastSeenAuth = newAuth; lastSeenAccuracy = newAcc
        guard let prevAuth, let prevAcc, (prevAuth != newAuth || prevAcc != newAcc) else { return }

        let wasAuthorized = prevAuth.isAuthorized
        if wasAuthorized && !newAuth.isAuthorized {
            // Revocation, observed (the time of revocation itself is unknown).
            stopUpdates()
            let before = probeState
            if probeState == .on || probeState == .paused { probeState = .blockedByOS }
            log("revocation_observed", before: before, after: probeState, actor: "probe_inferred")
        } else {
            log("authorization_change_observed", before: probeState, after: probeState, actor: "probe_inferred",
                note: "\(prevAuth.rawValue)/\(prevAcc.rawValue) -> \(newAuth.rawValue)/\(newAcc.rawValue)")
            if newAuth.isAuthorized {
                if awaitingOSPrompt && probeState == .on {
                    awaitingOSPrompt = false
                    startIfPossible()
                } else if probeState == .blockedByOS {
                    // Authorization returned in Settings: the participant must resume deliberately.
                    probeState = .paused
                    pausedIntervals.append((Date(), nil))
                }
            } else if awaitingOSPrompt && probeState == .on {
                awaitingOSPrompt = false
                probeState = .blockedByOS   // participant answered "do not allow"
            }
        }
    }

    private func log(_ action: String, before: ProbeState, after: ProbeState, actor: String, note: String? = nil) {
        // `note` carries only state labels and counts, never values.
        controlLog.append(ControlEvent(time: Date(), source: Self.sourceId,
                                       action: note.map { "\(action) (\($0))" } ?? action,
                                       probeBefore: before, probeAfter: after,
                                       osState: "\(os.rawValue) / \(accuracy.rawValue)", actor: actor))
    }

    private func accept(_ batch: [Incoming]) {
        guard probeState == .on, appActive else { return }
        for c in batch {
            guard c.horizontalAccuracy >= 0 else { discardedInvalid += 1; continue }
            if let last = lastAccepted, c.receiveTime.timeIntervalSince(last) < Self.minIntervalSeconds { continue }
            lastAccepted = c.receiveTime
            samples.append(LocationSample(
                eventTime: c.eventTime, receiveTime: c.receiveTime, latitude: c.latitude, longitude: c.longitude,
                horizontalAccuracy: c.horizontalAccuracy,
                speed: c.speed >= 0 ? c.speed : nil, course: c.course >= 0 ? c.course : nil,
                method: Self.method, delivery: "live",
                simulatedBySoftware: c.simulated, producedByAccessory: c.accessory, segment: segment))
        }
    }

    // MARK: CLLocationManagerDelegate (callbacks arrive on the thread the manager was created on: main)

    struct Incoming: Sendable {
        let eventTime: Date, receiveTime: Date
        let latitude: Double, longitude: Double, horizontalAccuracy: Double
        let speed: Double, course: Double
        let simulated: Bool?, accessory: Bool?
    }

    nonisolated func locationManagerDidChangeAuthorization(_ manager: CLLocationManager) {
        let auth = OSAuthorization(manager.authorizationStatus)
        let acc = OSAccuracy(manager.accuracyAuthorization)
        Task { @MainActor in self.apply(auth: auth, accuracy: acc) }
    }

    nonisolated func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        let now = Date()
        let batch = locations.map { l in
            Incoming(eventTime: l.timestamp, receiveTime: now,
                     latitude: l.coordinate.latitude, longitude: l.coordinate.longitude,
                     horizontalAccuracy: l.horizontalAccuracy, speed: l.speed, course: l.course,
                     simulated: l.sourceInformation?.isSimulatedBySoftware,
                     accessory: l.sourceInformation?.isProducedByAccessory)
        }
        Task { @MainActor in self.accept(batch) }
    }

    nonisolated func locationManager(_ manager: CLLocationManager, didFailWithError error: Error) {
        // Errors are not logged with values. A denied error is handled via the authorization callback.
        let code = (error as? CLError)?.code.rawValue ?? -1
        Task { @MainActor in self.log("error_observed", before: self.probeState, after: self.probeState,
                                      actor: "probe_inferred", note: "CLError \(code)") }
    }
}
