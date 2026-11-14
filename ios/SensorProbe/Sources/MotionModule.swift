import CoreMotion
import Foundation
import Observation

// MOT-01 (Motion), foreground only. docs/sensor-probe-spec.md sections 3, 5, 8.
// TEST BUILD, not cleared for real data (gate R): records are kept IN MEMORY ONLY, are lost when
// the app exits, and there is no export, network or transfer code. Control events never hold values.
//
// Three separable capabilities: (a) bounded history query of activity, (b) live activity updates,
// (c) pedometer (aggregate counts over a window: history query per day, and live cumulative updates).
// Activity segments are INTERVALS (start now, end = start of the next segment of the same
// acquisition); pedometer records are AGGREGATES over a window. They are never mixed.

/// Authorization as reported by the OS for Core Motion (spec 3.1). The headers expose a status for
/// the activity manager and for the pedometer separately; both are shown.
enum MotionAuth: String, Sendable {
    case notDetermined = "not_determined"
    case restricted
    case denied
    case authorized
    case unknown

    init(_ s: CMAuthorizationStatus) {
        switch s {
        case .notDetermined: self = .notDetermined
        case .restricted: self = .restricted
        case .denied: self = .denied
        case .authorized: self = .authorized
        @unknown default: self = .unknown
        }
    }
}

enum MotionConfidence: Int, Sendable { case low = 0, medium, high, unknown = -1 }

/// How a record reached the probe (spec 3.3): live observation, a participant-initiated history
/// import, or an import of the interval the participant paused.
enum MotionAcquisition: String, Sendable { case live, historyImport = "history_import", backfillAfterPause = "backfill_after_pause" }

/// A device-reported activity interval. `end` is nil while it is the latest one of its group (open).
struct ActivitySegment: Sendable {
    let start: Date
    let label: String            // device-reported label(s), not observed behavior
    let confidence: MotionConfidence
    let acquisition: MotionAcquisition
    let run: Int                 // live run number, 0 for imports
}

/// An aggregate over a window (granularity = aggregate). Live records are cumulative since `start`.
struct PedometerWindow: Sendable {
    let start: Date
    let end: Date
    let steps: Int
    let distanceMeters: Double?
    let cumulativeLive: Bool
    let acquisition: MotionAcquisition
    let run: Int                 // live run number, 0 for imports
}

/// What a history import actually returned (never a claimed window).
struct ImportReport: Identifiable {
    let id = UUID()
    let at: Date
    let kind: MotionAcquisition
    let requestedFrom: Date
    let requestedTo: Date
    var activityReturned = 0
    var activityAdded = 0
    var oldestActivity: Date?
    var latestActivity: Date?
    var pedometerWindowsAsked = 0
    var pedometerWindowsReturned = 0
    var pedometerDaysWithSteps = 0
    var errors: [Int] = []       // CMError codes only
    var pending = 0
}

@MainActor
@Observable
final class MotionModule {
    static let sourceId = "MOT-01"
    /// Predeclared (spec 4/5: recorded, not hidden). The 7-day figure is quoted from the iOS 27.2
    /// CoreMotion headers; the real window is measured by the owner test, not claimed.
    static let method = "foreground_live_updates + history_query_per_day"
    static let documentedHistoryDays = 7

    private(set) var probeState: ProbeState = .off
    private(set) var activityAuth: MotionAuth = .unknown
    private(set) var pedometerAuth: MotionAuth = .unknown
    private(set) var osObservedAt: Date?
    private(set) var activityAvailable = false
    private(set) var stepsAvailable = false
    private(set) var distanceAvailable = false
    private(set) var segments: [ActivitySegment] = []
    private(set) var pedometer: [PedometerWindow] = []
    private(set) var controlLog: [ControlEvent] = []
    private(set) var pausedIntervals: [(from: Date, to: Date?)] = []
    private(set) var imports: [ImportReport] = []
    private(set) var duplicatesDropped = 0
    private(set) var errorCodes: [Int] = []
    private(set) var isUpdating = false

    @ObservationIgnored private let activityManager = CMMotionActivityManager()
    @ObservationIgnored private let pedometerManager = CMPedometer()
    @ObservationIgnored private let queue = OperationQueue()
    @ObservationIgnored private var run = 0
    @ObservationIgnored private var appActive = false
    @ObservationIgnored private var awaitingOSPrompt = false
    @ObservationIgnored private var pollTask: Task<Void, Never>?
    @ObservationIgnored private var lastSeenActivityAuth: MotionAuth?

    init() {
        queue.maxConcurrentOperationCount = 1
        refreshOSState()
    }

    // MARK: derived

    var authorizedByOS: Bool { activityAuth == .authorized }
    var osLabel: String {
        "activité: \(activityAuth.rawValue) · podomètre: \(pedometerAuth.rawValue)"
    }
    var availabilityLabel: String {
        "activité \(activityAvailable ? "disponible" : "non disponible") · pas \(stepsAvailable ? "disponibles" : "non disponibles") · distance \(distanceAvailable ? "disponible" : "non disponible")"
    }
    var isCollecting: Bool { probeState == .on && authorizedByOS && appActive && isUpdating }

    var confidenceCounts: (low: Int, medium: Int, high: Int, unknown: Int) {
        var c = (low: 0, medium: 0, high: 0, unknown: 0)
        for s in segments {
            switch s.confidence { case .low: c.low += 1; case .medium: c.medium += 1; case .high: c.high += 1; case .unknown: c.unknown += 1 }
        }
        return c
    }
    func count(_ a: MotionAcquisition) -> Int { segments.filter { $0.acquisition == a }.count }
    func windows(_ a: MotionAcquisition) -> Int { pedometer.filter { $0.acquisition == a }.count }
    var unknownLabelCount: Int { segments.filter { $0.label == "unknown" }.count }
    var oldestSegment: Date? { segments.map(\.start).min() }
    var latestSegment: Date? { segments.map(\.start).max() }
    var totalSteps: Int { pedometer.filter { !$0.cumulativeLive }.reduce(0) { $0 + $1.steps } }
    var liveSteps: Int { pedometer.filter(\.cumulativeLive).reduce(0) { $0 + $1.steps } }
    var runCount: Int { Set(segments.filter { $0.acquisition == .live }.map(\.run) + pedometer.filter(\.cumulativeLive).map(\.run)).count }
    var hasRecords: Bool { !segments.isEmpty || !pedometer.isEmpty }
    var recordCount: Int { segments.count + pedometer.count }
    /// Distinct calendar days with at least one history-returned activity segment start.
    var activityDaysCovered: Int {
        Set(segments.filter { $0.acquisition != .live }.map { Calendar.current.startOfDay(for: $0.start) }).count
    }

    // MARK: participant actions

    func logExplained() { log("explained", before: probeState, after: probeState, actor: "participant") }

    func declinePrePrompt() {
        log("declined_preprompt", before: probeState, after: probeState, actor: "participant")
        // Nothing is called on Core Motion: no OS dialog.
    }

    /// Called only after "Continuer vers la demande du système" for live collection.
    func enableAfterPrePrompt() {
        let before = probeState
        refreshOSState()
        probeState = .on
        log("enabled", before: before, after: .on, actor: "participant")
        guard activityAvailable else {
            probeState = .blockedByOS
            log("unsupported_observed", before: .on, after: .blockedByOS, actor: "probe_inferred")
            return
        }
        switch activityAuth {
        case .notDetermined:
            awaitingOSPrompt = true
            log("os_prompt_requested", before: .on, after: .on, actor: "probe_inferred")
            startIfPossible(allowUndetermined: true)   // the first Core Motion call raises the OS dialog
            startPolling()
        case .authorized:
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

    /// Resume starts from now. `importPausedInterval` is the participant's separate answer
    /// (default no, spec 3.3); when yes the OS-held records for the interval are labelled backfill.
    func resume(importPausedInterval: Bool) {
        guard probeState == .paused else { return }
        refreshOSState()
        let interval = pausedIntervals.last
        closePausedInterval()
        probeState = .on
        log(importPausedInterval ? "backfill_chosen_yes" : "backfill_chosen_no", before: .paused, after: .paused, actor: "participant")
        log("resumed", before: .paused, after: .on, actor: "participant")
        guard authorizedByOS else { probeState = .blockedByOS; return }
        startIfPossible()
        if importPausedInterval, let from = interval?.from {
            runImport(kind: .backfillAfterPause, from: from, to: Date())
        }
    }

    /// Participant-initiated history import (after the pre-prompt). Probe state is unchanged.
    func importHistoryAfterPrePrompt() {
        refreshOSState()
        guard activityAvailable || stepsAvailable else {
            log("unsupported_observed", before: probeState, after: probeState, actor: "probe_inferred"); return
        }
        if activityAuth == .notDetermined {
            log("os_prompt_requested", before: probeState, after: probeState, actor: "probe_inferred")
            startPolling()
        }
        log("history_import_requested", before: probeState, after: probeState, actor: "participant")
        let to = Date()
        runImport(kind: .historyImport, from: to.addingTimeInterval(-Double(Self.documentedHistoryDays) * 86400 + 60), to: to)
    }

    func deleteAll() {
        let n = recordCount
        segments.removeAll(keepingCapacity: false)
        pedometer.removeAll(keepingCapacity: false)
        imports.removeAll()
        duplicatesDropped = 0
        errorCodes.removeAll()
        run = 0
        log("deleted_all", before: probeState, after: probeState, actor: "participant", note: "\(n) records; iOS-held history not deleted")
    }

    // MARK: lifecycle

    func appDidBecomeActive() {
        appActive = true
        refreshOSState()
        if probeState == .on, authorizedByOS { startIfPossible() }
    }

    func appDidLeaveForeground() {
        appActive = false
        stopUpdates()   // no background mode: the gap is ours and visible
    }

    // MARK: live updates

    private func startIfPossible(allowUndetermined: Bool = false) {
        guard probeState == .on, appActive, !isUpdating else { return }
        guard authorizedByOS || (allowUndetermined && activityAuth == .notDetermined) else { return }
        run += 1
        isUpdating = true
        let now = Date()
        let r = run
        if activityAvailable {
            activityManager.startActivityUpdates(to: queue, withHandler: Self.liveActivityHandler(self, run: r))
        }
        if stepsAvailable {
            pedometerManager.startUpdates(from: now, withHandler: Self.livePedometerHandler(self, run: r, since: now))
        }
    }

    private func stopUpdates() {
        guard isUpdating else { return }
        activityManager.stopActivityUpdates()
        pedometerManager.stopUpdates()
        isUpdating = false
    }

    private func closePausedInterval() {
        if let i = pausedIntervals.indices.last, pausedIntervals[i].to == nil { pausedIntervals[i].to = Date() }
    }

    // MARK: history import

    private func runImport(kind: MotionAcquisition, from rawFrom: Date, to: Date) {
        let floor = to.addingTimeInterval(-Double(Self.documentedHistoryDays) * 86400 + 60)
        let from = max(rawFrom, floor)   // never ask beyond the documented window
        guard from < to else {
            log("history_import_skipped", before: probeState, after: probeState, actor: "probe_inferred", note: "interval older than documented window")
            return
        }
        var report = ImportReport(at: Date(), kind: kind, requestedFrom: from, requestedTo: to)
        let id = report.id
        var pedChunks: [(Date, Date)] = []
        if stepsAvailable {
            var cursor = from
            let cal = Calendar.current
            while cursor < to {
                let nextMidnight = cal.date(byAdding: .day, value: 1, to: cal.startOfDay(for: cursor)) ?? to
                let end = min(nextMidnight, to)
                pedChunks.append((cursor, end)); cursor = end
            }
        }
        report.pedometerWindowsAsked = pedChunks.count
        report.pending = (activityAvailable ? 1 : 0) + pedChunks.count
        imports.append(report)
        if activityAvailable {
            activityManager.queryActivityStarting(from: from, to: to, to: queue, withHandler: Self.activityQueryHandler(self, id: id, kind: kind))
        }
        for (a, b) in pedChunks {
            pedometerManager.queryPedometerData(from: a, to: b, withHandler: Self.pedometerQueryHandler(self, id: id, kind: kind, from: a, to: b))
        }
    }

    // nonisolated factories so the handler closures are not main-actor isolated (they run on `queue`).
    nonisolated private static func liveActivityHandler(_ m: MotionModule, run: Int) -> CMMotionActivityHandler {
        return { a in
            let rec = a.map(Self.snapshot)
            Task { @MainActor in if let rec { m.acceptLive(rec, run: run) } }
        }
    }
    nonisolated private static func livePedometerHandler(_ m: MotionModule, run: Int, since: Date) -> CMPedometerHandler {
        return { d, e in
            let snap = d.map { PedSnap(start: $0.startDate, end: $0.endDate, steps: $0.numberOfSteps.intValue, distance: $0.distance?.doubleValue) }
            let code = (e as NSError?)?.code
            Task { @MainActor in m.acceptLivePedometer(snap, run: run, code: code) }
        }
    }
    nonisolated private static func activityQueryHandler(_ m: MotionModule, id: UUID, kind: MotionAcquisition) -> CMMotionActivityQueryHandler {
        return { list, e in
            let recs = (list ?? []).map(Self.snapshot)
            let code = (e as NSError?)?.code
            Task { @MainActor in m.finishActivityQuery(id: id, kind: kind, recs: recs, code: code) }
        }
    }
    nonisolated private static func pedometerQueryHandler(_ m: MotionModule, id: UUID, kind: MotionAcquisition, from: Date, to: Date) -> CMPedometerHandler {
        return { d, e in
            let snap = d.map { PedSnap(start: $0.startDate, end: $0.endDate, steps: $0.numberOfSteps.intValue, distance: $0.distance?.doubleValue) }
            let code = (e as NSError?)?.code
            Task { @MainActor in m.finishPedometerQuery(id: id, kind: kind, snap: snap, code: code) }
        }
    }

    struct ActSnap: Sendable { let start: Date; let label: String; let confidence: MotionConfidence }
    struct PedSnap: Sendable { let start: Date; let end: Date; let steps: Int; let distance: Double? }

    nonisolated private static func snapshot(_ a: CMMotionActivity) -> ActSnap {
        var parts: [String] = []
        if a.unknown { parts.append("unknown") }
        if a.stationary { parts.append("stationary") }
        if a.walking { parts.append("walking") }
        if a.running { parts.append("running") }
        if a.cycling { parts.append("cycling") }
        if a.automotive { parts.append("automotive") }
        let conf: MotionConfidence
        switch a.confidence {
        case .low: conf = .low
        case .medium: conf = .medium
        case .high: conf = .high
        @unknown default: conf = .unknown
        }
        return ActSnap(start: a.startDate, label: parts.isEmpty ? "moving_unclassified" : parts.joined(separator: "+"), confidence: conf)
    }

    // MARK: accepting records (main actor)

    private func acceptLive(_ r: ActSnap, run: Int) {
        guard probeState == .on, appActive, isUpdating else { return }
        add(ActivitySegment(start: r.start, label: r.label, confidence: r.confidence, acquisition: .live, run: run))
    }

    private func acceptLivePedometer(_ d: PedSnap?, run: Int, code: Int?) {
        if let code { note(error: code) }
        guard let d, probeState == .on, appActive, isUpdating else { return }
        let w = PedometerWindow(start: d.start, end: d.end, steps: d.steps, distanceMeters: d.distance,
                                cumulativeLive: true, acquisition: .live, run: run)
        if let i = pedometer.lastIndex(where: { $0.cumulativeLive && $0.run == run }) { pedometer[i] = w } else { pedometer.append(w) }
    }

    private func add(_ s: ActivitySegment) {
        if segments.contains(where: { $0.start == s.start && $0.label == s.label }) { duplicatesDropped += 1; return }
        segments.append(s)
    }

    private func finishActivityQuery(id: UUID, kind: MotionAcquisition, recs: [ActSnap], code: Int?) {
        guard let i = imports.firstIndex(where: { $0.id == id }) else { return }   // deleted meanwhile
        imports[i].pending -= 1
        if let code { imports[i].errors.append(code); note(error: code) }
        imports[i].activityReturned = recs.count
        imports[i].oldestActivity = recs.map(\.start).min()
        imports[i].latestActivity = recs.map(\.start).max()
        let before = segments.count
        for r in recs { add(ActivitySegment(start: r.start, label: r.label, confidence: r.confidence, acquisition: kind, run: 0)) }
        imports[i].activityAdded = segments.count - before
        refreshOSState()
        log("history_import_activity_done", before: probeState, after: probeState, actor: "probe_inferred",
            note: "\(recs.count) returned\(code.map { ", CMError \($0)" } ?? "")")
    }

    private func finishPedometerQuery(id: UUID, kind: MotionAcquisition, snap: PedSnap?, code: Int?) {
        guard let i = imports.firstIndex(where: { $0.id == id }) else { return }
        imports[i].pending -= 1
        if let code { imports[i].errors.append(code); note(error: code) }
        if let s = snap {
            imports[i].pedometerWindowsReturned += 1
            if s.steps > 0 { imports[i].pedometerDaysWithSteps += 1 }
            pedometer.append(PedometerWindow(start: s.start, end: s.end, steps: s.steps, distanceMeters: s.distance,
                                             cumulativeLive: false, acquisition: kind, run: 0))
        }
        if imports[i].pending == 0 {
            refreshOSState()
            log("history_import_pedometer_done", before: probeState, after: probeState, actor: "probe_inferred",
                note: "\(imports[i].pedometerWindowsReturned)/\(imports[i].pedometerWindowsAsked) windows")
        }
    }

    private func note(error code: Int) {
        errorCodes.append(code)
        log("error_observed", before: probeState, after: probeState, actor: "probe_inferred", note: "CMError \(code)")
    }

    // MARK: OS state

    private func startPolling() {
        pollTask?.cancel()
        pollTask = Task { [weak self] in
            // The first Core Motion call raises the system dialog; there is no delegate callback,
            // so the status is re-read for up to 90 s (and on every return to foreground).
            for _ in 0..<90 {
                try? await Task.sleep(for: .seconds(1))
                guard let self, !Task.isCancelled else { return }
                self.refreshOSState()
                if self.activityAuth != .notDetermined { return }
            }
        }
    }

    private func refreshOSState() {
        activityAvailable = CMMotionActivityManager.isActivityAvailable()
        stepsAvailable = CMPedometer.isStepCountingAvailable()
        distanceAvailable = CMPedometer.isDistanceAvailable()
        apply(activity: MotionAuth(CMMotionActivityManager.authorizationStatus()),
              pedometer: MotionAuth(CMPedometer.authorizationStatus()))
    }

    private func apply(activity new: MotionAuth, pedometer newPed: MotionAuth) {
        let prev = lastSeenActivityAuth
        activityAuth = new; pedometerAuth = newPed; osObservedAt = Date(); lastSeenActivityAuth = new
        guard let prev, prev != new else { return }
        if prev == .authorized && new != .authorized {
            stopUpdates()
            let before = probeState
            if probeState == .on || probeState == .paused { probeState = .blockedByOS }
            log("revocation_observed", before: before, after: probeState, actor: "probe_inferred")
        } else {
            log("authorization_change_observed", before: probeState, after: probeState, actor: "probe_inferred",
                note: "\(prev.rawValue) -> \(new.rawValue)")
            if new == .authorized {
                if awaitingOSPrompt && probeState == .on {
                    awaitingOSPrompt = false
                    startIfPossible()
                } else if probeState == .blockedByOS {
                    probeState = .paused   // deliberate resume required, never a silent restart
                    pausedIntervals.append((Date(), nil))
                }
            } else if awaitingOSPrompt && probeState == .on {
                awaitingOSPrompt = false
                stopUpdates()
                probeState = .blockedByOS   // participant answered "do not allow"
            }
        }
    }

    private func log(_ action: String, before: ProbeState, after: ProbeState, actor: String, note: String? = nil) {
        // `note` carries only state labels, counts and error codes, never values.
        controlLog.append(ControlEvent(time: Date(), source: Self.sourceId,
                                       action: note.map { "\(action) (\($0))" } ?? action,
                                       probeBefore: before, probeAfter: after,
                                       osState: osLabel, actor: actor))
    }
}
