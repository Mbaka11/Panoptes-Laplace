import SwiftUI

/// Sensor Probe, scaffold stage (D-044). It reports the build environment (ENV-01) and
/// lists every source as "off". It requests no permission and collects nothing.
@main
struct SensorProbeApp: App {
    var body: some Scene {
        WindowGroup { ContentView() }
    }
}
