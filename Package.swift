// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "AV1Policy",
    platforms: [
        .iOS(.v14),
        .macOS(.v11)
    ],
    products: [
        .library(
            name: "AV1Policy",
            targets: ["AV1Policy"]
        ),
    ],
    dependencies: [],
    targets: [
        .target(
            name: "AV1Policy",
            path: "ios/AV1Policy/Sources/AV1Policy"
        ),
        .testTarget(
            name: "AV1PolicyTests",
            dependencies: ["AV1Policy"],
            path: "ios/AV1Policy/Tests/AV1PolicyTests"
        ),
    ]
)
