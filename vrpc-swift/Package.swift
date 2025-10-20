// swift-tools-version: 5.9
// The swift-tools-version declares the minimum version of Swift required to build this package.

import PackageDescription

let package = Package(
    name: "VuerRPC",
    platforms: [
        .macOS(.v13),
        .iOS(.v16),
        .tvOS(.v16),
        .watchOS(.v9)
    ],
    products: [
        .library(
            name: "VuerRPC",
            targets: ["VuerRPC"]
        ),
    ],
    dependencies: [
        // MessagePack serialization
        .package(url: "https://github.com/Flight-School/MessagePack.git", from: "1.2.0"),
    ],
    targets: [
        .target(
            name: "VuerRPC",
            dependencies: [
                .product(name: "MessagePack", package: "MessagePack"),
            ]
        ),
        .testTarget(
            name: "VuerRPCTests",
            dependencies: ["VuerRPC"]
        ),
    ]
)
