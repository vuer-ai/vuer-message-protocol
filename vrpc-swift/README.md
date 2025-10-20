# VuerRPC-Swift: Swift Implementation of the Vuer Message Protocol

[![Swift](https://img.shields.io/badge/Swift-5.9+-orange.svg)](https://swift.org)
[![Platforms](https://img.shields.io/badge/Platforms-iOS%20%7C%20macOS%20%7C%20tvOS%20%7C%20watchOS-blue.svg)](https://swift.org)
[![SPM](https://img.shields.io/badge/SPM-compatible-brightgreen.svg)](https://swift.org/package-manager)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A lightweight, cross-language messaging and RPC protocol designed for use with Vuer and Zaku. This is the Swift implementation with full support for MessagePack serialization, extensible type systems, and async RPC.

## Features

- **MessagePack Serialization**: Efficient binary encoding for cross-language compatibility
- **Extensible Type System**: Register custom types with ZData encoding
- **Async RPC Support**: Request-response correlation with Swift async/await
- **Built-in Types**: Support for Swift native types
- **Type Conversion Fallbacks**: Graceful handling of types not available in Swift
- **Modern Swift**: Uses Swift 5.9+ with modern concurrency (async/await, actors)
- **Cross-Platform**: Supports iOS, macOS, tvOS, and watchOS

## Requirements

- Swift 5.9+
- iOS 16.0+ / macOS 13.0+ / tvOS 16.0+ / watchOS 9.0+

## Installation

### Swift Package Manager

Add VuerRPC to your `Package.swift`:

```swift
dependencies: [
    .package(url: "https://github.com/vuer-ai/vuer-message-protocol.git", from: "0.1.0")
]
```

Then add it to your target dependencies:

```swift
targets: [
    .target(
        name: "YourTarget",
        dependencies: [
            .product(name: "VuerRPC", package: "vuer-message-protocol")
        ]
    )
]
```

### Xcode

1. File → Add Package Dependencies
2. Enter repository URL: `https://github.com/vuer-ai/vuer-message-protocol`
3. Select version and add to your project

## Quick Start

```swift
import VuerRPC

// Create a message
let msg = Message(
    etype: "CLICK",
    value: AnyCodable(["x": 100, "y": 200])
)

// Serialize to MessagePack
let data = try serializeMessage(msg)

// Deserialize
let restored = try deserializeMessage(data)

print("Event type: \(restored.etype)")
```

## Core Types

### Message Envelopes

```swift
// Generic message with all fields
let msg = Message(
    etype: "UPDATE",
    data: AnyCodable(["status": "ready"])
)

// Client-to-server event
let clientEvent = ClientEvent(
    etype: "CLICK",
    value: AnyCodable(["x": 100, "y": 200])
)

// Server-to-client event
let serverEvent = ServerEvent(
    etype: "UPDATE",
    data: AnyCodable(["users": 42])
)
```

### RPC Requests/Responses

```swift
// Create RPC request
let rpcReq = RPCRequest(
    etype: "render",
    rtype: "rpc-12345",
    kwargs: ["seed": 12345]
)

// Create RPC response
let rpcResp = RPCResponse.success(
    etype: "rpc-12345",
    data: AnyCodable(["result": "done"])
)
```

### Vuer Components

```swift
// Build a component tree
var sphere = VuerComponent(tag: "sphere")
sphere.setProperty(key: "radius", value: 1.0)
sphere.setProperty(key: "color", value: "#ff0000")

var scene = VuerComponent(tag: "scene")
scene.addChild(sphere)
scene.setProperty(key: "background", value: "#000000")

// Serialize the component tree
let data = try serializeComponent(scene)
```

## Async RPC

VuerRPC uses Swift's modern async/await for RPC operations:

```swift
import VuerRPC

func performRPC() async throws {
    let manager = RPCManager()

    // Send an RPC request
    let (req, responseTask) = try await manager.request(
        etype: "render",
        kwargs: ["quality": "high"],
        timeout: 5.0
    )

    // ... send req over the network ...

    // Await the response
    let response = try await responseTask.value
    print("Result: \(response.data)")
}
```

## Custom Type Registration

The type registry allows you to encode/decode custom types:

```swift
import VuerRPC

// Register a custom datetime type
let registration = TypeRegistration(
    ztype: "datetime",
    encoder: { value in
        var zdata = ZData(ztype: "datetime")
        if let date = value as? Date {
            zdata.setField(key: "iso", value: AnyCodable(date.ISO8601Format()))
        }
        return zdata
    },
    decoder: { zdata in
        guard let iso = zdata.getField(key: "iso")?.value as? String,
              let date = try? Date(iso, strategy: .iso8601) else {
            throw VuerRPCError.typeConversionError("Invalid date format")
        }
        return date
    }
)

await globalTypeRegistry.register(registration)
```

## ZData Encoding

ZData is a wrapper format for encoding types that don't have direct Swift equivalents:

```swift
// Create ZData for a custom type
var zdata = ZData(ztype: "custom.Type")
zdata.b = Data([1, 2, 3, 4])
zdata.dtype = "uint8"
zdata.shape = [2, 2]
zdata.setField(key: "metadata", value: AnyCodable(["version": "1.0"]))

// Serialize to MessagePack
let data = try serialize(zdata)
```

## Error Handling

VuerRPC uses Swift's typed error handling:

```swift
do {
    let data = try serializeMessage(message)
} catch VuerRPCError.serializationError(let message) {
    print("Serialization failed: \(message)")
} catch {
    print("Unexpected error: \(error)")
}
```

## Testing

Run tests using Swift Package Manager:

```bash
# Run all tests
swift test

# Run with verbose output
swift test --verbose

# Generate code coverage
swift test --enable-code-coverage
```

### Xcode

1. Open Package.swift in Xcode
2. Product → Test (⌘U)

## Package Manager & Tooling

### Modern Swift Tooling (2025)

This project uses the latest Swift tooling best practices:

- **Package Manager**: Swift Package Manager (SPM) - built into Swift
- **Test Framework**: XCTest - built into Swift
- **Build System**: SwiftPM build system
- **Platforms**: iOS, macOS, tvOS, watchOS

### Building

```bash
# Debug build
swift build

# Release build (optimized)
swift build -c release

# Clean build artifacts
swift package clean
```

### Code Generation

```bash
# Generate Xcode project (if needed)
swift package generate-xcodeproj

# Update dependencies
swift package update
```

## AnyCodable

VuerRPC includes `AnyCodable`, a type-erased wrapper for handling dynamic JSON-like values:

```swift
// Create from literals
let bool: AnyCodable = true
let number: AnyCodable = 42
let string: AnyCodable = "hello"
let array: AnyCodable = [1, 2, 3]
let dict: AnyCodable = ["key": "value"]

// Access underlying values
if let value = number.value as? Int {
    print("Number: \(value)")
}
```

## Cross-Language Compatibility

VuerRPC-Swift is designed to be compatible with:

- **vrpc-ts** (TypeScript/JavaScript)
- **vrpc-py** (Python)
- **vrpc-rs** (Rust)

All implementations use MessagePack for serialization and follow the same ZData encoding conventions.

## Architecture

### Concurrency Model

- **Actor-based Type Registry**: Thread-safe type registration using Swift actors
- **Async/Await RPC**: Modern async/await for asynchronous operations
- **Sendable**: All public types conform to `Sendable` for safe concurrency

### Serialization

- Uses MessagePack for efficient binary encoding
- Supports nested structures and component trees
- Type-safe encoding/decoding with `Codable`

## Examples

```swift
import VuerRPC

// Example 1: Simple message
let msg = Message(etype: "USER_CLICK", value: AnyCodable(["x": 150, "y": 200]))
let data = try serializeMessage(msg)
print("Serialized \(data.count) bytes")

// Example 2: Component tree
var sphere = VuerComponent(tag: "sphere")
sphere.setProperty(key: "radius", value: 1.0)

var scene = VuerComponent(tag: "scene")
scene.addChild(sphere)

let componentData = try serializeComponent(scene)

// Example 3: Async RPC
let manager = RPCManager()
let (req, task) = try await manager.request(etype: "render", timeout: 5.0)

// ... send req ...

let response = try await task.value
print("RPC result: \(response.data)")
```

## Known Limitations

### MessagePack + AnyCodable

While `AnyCodable` provides flexibility, it's recommended to use strongly-typed structs for production:

```swift
struct MyPayload: Codable {
    let x: Int
    let y: Int
}

// Better type safety
let payload = MyPayload(x: 100, y: 200)
```

## Documentation

- [API Documentation](https://vuer-ai.github.io/vuer-message-protocol/vrpc-swift)
- [Protocol Specification](../README.md)
- [Implementation Guide](../notes/IMPLEMENTATION_GUIDE.md)

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](../LICENSE) for details

## Author

Ge Yang

---

For more information about the Vuer Message Protocol, see the [main repository](https://github.com/vuer-ai/vuer-message-protocol).
