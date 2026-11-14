import SwiftUI
import UIKit

/// Per-source participant state from docs/sensor-probe-spec.md 3.2. At scaffold stage every
/// source is `off`: the probe has not asked the OS for anything.
enum ProbeState: String { case off, on, paused, blockedByOS = "blocked_by_os" }

struct Source: Identifiable {
    let id: String      // protocol case id
    let name: String
    let state: ProbeState
}

@MainActor
struct EnvironmentReport {
    let osVersion = UIDevice.current.systemVersion
    let model: String = {
        var info = utsname(); uname(&info)
        return withUnsafePointer(to: &info.machine) {
            $0.withMemoryRebound(to: CChar.self, capacity: 1) { String(cString: $0) }
        }
    }()
    let appVersion = Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "unknown"
    let isSimulator: Bool = {
        #if targetEnvironment(simulator)
        return true
        #else
        return false
        #endif
    }()
}

struct ContentView: View {
    private let env = EnvironmentReport()
    @State private var location = LocationModule()
    @State private var motion = MotionModule()
    @Environment(\.scenePhase) private var scenePhase
    private let sources = [
        Source(id: "HLT-01", name: "Health", state: .off),
        Source(id: "EVT-01", name: "Calendar and reminders", state: .off),
        Source(id: "SCT-01", name: "Screen Time (separate gate)", state: .off),
    ]

    var body: some View {
        NavigationStack {
            List {
                Section {
                    Text("TEST BUILD: not cleared for real data. Location (LOC-01) and Motion (MOT-01) collect only when you enable them, in memory only, foreground only. Other sources: nothing collected, no permission requested.")
                        .font(.footnote).foregroundStyle(.orange)
                }
                Section("Environment (ENV-01)") {
                    row("Device model", env.model)
                    row("iOS", env.osVersion)
                    row("App version", env.appVersion)
                    row("Running on", env.isSimulator ? "simulator" : "device")
                }
                Section("Sources") {
                    NavigationLink {
                        LocationView(module: location)
                    } label: {
                        VStack(alignment: .leading, spacing: 2) {
                            Text("Location")
                            Text("LOC-01 · probe state: \(location.probeState.rawValue) · OS state: \(location.osLabel)")
                                .font(.caption).foregroundStyle(.secondary)
                        }
                    }
                    NavigationLink {
                        MotionView(module: motion)
                    } label: {
                        VStack(alignment: .leading, spacing: 2) {
                            Text("Motion")
                            Text("MOT-01 · probe state: \(motion.probeState.rawValue) · OS state: \(motion.osLabel)")
                                .font(.caption).foregroundStyle(.secondary)
                        }
                    }
                    ForEach(sources) { s in
                        VStack(alignment: .leading, spacing: 2) {
                            Text(s.name)
                            Text("\(s.id) · probe state: \(s.state.rawValue) · OS state: not requested")
                                .font(.caption).foregroundStyle(.secondary)
                        }
                    }
                }
            }
            .navigationTitle("Sensor Probe")
            .onChange(of: scenePhase, initial: true) { _, phase in
                if phase == .active { location.appDidBecomeActive(); motion.appDidBecomeActive() } else { location.appDidLeaveForeground(); motion.appDidLeaveForeground() }
            }
        }
    }

    private func row(_ k: String, _ v: String) -> some View {
        HStack { Text(k); Spacer(); Text(v).foregroundStyle(.secondary).monospaced() }
    }
}
