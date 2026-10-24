import SwiftUI
import AppKit

@main
struct ProofreadApp: App {
    init() {
        NSApplication.shared.setActivationPolicy(.regular)
        DispatchQueue.main.async { NSApplication.shared.activate(ignoringOtherApps: true) }
    }

    var body: some Scene {
        WindowGroup("Proofread") {
            ContentView()
                .frame(minWidth: 720, minHeight: 640)
        }
        .windowStyle(.hiddenTitleBar)
    }
}
