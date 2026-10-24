// swift-tools-version:6.2
import PackageDescription

let package = Package(
    name: "Proofread",
    platforms: [.macOS(.v26)],
    targets: [.executableTarget(name: "Proofread", swiftSettings: [.swiftLanguageMode(.v5)])]
)
