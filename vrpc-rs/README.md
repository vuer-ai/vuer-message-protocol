# VMP-RS: Rust Implementation of the Vuer Message Protocol

[![Crates.io](https://img.shields.io/crates/v/vuer-rpc.svg)](https://crates.io/crates/vuer-rpc)
[![Documentation](https://docs.rs/vuer-rpc/badge.svg)](https://docs.rs/vuer-rpc)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A lightweight, cross-language messaging and RPC protocol designed for use with Vuer and Zaku. This is the Rust implementation with full support for MessagePack serialization, extensible type systems, and async RPC.

## Features

- **MessagePack Serialization**: Efficient binary encoding for cross-language compatibility
- **Extensible Type System**: Register custom types with ZData encoding
- **RPC Support**: Request-response correlation with async/await using Tokio
- **Built-in Types**: Optional support for NumPy-like arrays (ndarray) and images
- **Type Conversion Fallbacks**: Graceful handling of types not available in Rust
- **Zero-cost Abstractions**: Performance-oriented design with minimal overhead
- **Modern Rust**: Uses Rust 2024 edition with latest best practices

## Installation

Add this to your `Cargo.toml`:

```toml
[dependencies]
vuer-rpc = "0.1"

# For async RPC support
vuer-rpc = { version = "0.1", features = ["tokio"] }

# For all features including ndarray and image support
vuer-rpc = { version = "0.1", features = ["full"] }
```

## Quick Start

```rust
use vuer_rpc::prelude::*;
use serde_json::json;

fn main() -> Result<()> {
    // Create a message
    let msg = Message::new("CLICK")
        .with_value(json!({"x": 100, "y": 200}));

    // Serialize to MessagePack
    let bytes = serialize_message(&msg)?;

    // Deserialize
    let restored: Message = deserialize_message(&bytes)?;

    println!("Event type: {}", restored.etype);
    Ok(())
}
```

## Core Types

### Message Envelopes

```rust
// Generic message with all fields
let msg = Message::new("UPDATE")
    .with_data(json!({"status": "ready"}));

// Client-to-server event
let client_event = ClientEvent::new("CLICK", json!({"x": 100, "y": 200}));

// Server-to-client event
let server_event = ServerEvent::new("UPDATE", json!({"users": 42}));
```

### RPC Requests/Responses

```rust
use std::collections::HashMap;

// Create RPC request
let mut kwargs = HashMap::new();
kwargs.insert("seed".to_string(), json!(12345));

let rpc_req = RpcRequest::new("render", "rpc-12345")
    .with_kwargs(kwargs);

// Create RPC response
let rpc_resp = RpcResponse::success("rpc-12345", json!({"result": "done"}));
```

### Vuer Components

```rust
// Build a component tree
let sphere = VuerComponent::new("sphere")
    .with_prop("radius", json!(1.0))
    .with_prop("color", json!("#ff0000"));

let scene = VuerComponent::new("scene")
    .with_child(sphere)
    .with_prop("background", json!("#000000"));

// Serialize the component tree
let bytes = serialize_component(&scene)?;
```

## Async RPC (with Tokio)

```rust
use vuer_rpc::prelude::*;
use std::time::Duration;

#[tokio::main]
async fn main() -> Result<()> {
    let manager = RpcManager::new();

    // Send an RPC request
    let (req, response_fut) = manager
        .request("render", None, None, Duration::from_secs(5))
        .await?;

    // ... send req over the network ...

    // Await the response
    let response = response_fut.await?;
    println!("Result: {:?}", response.data);

    Ok(())
}
```

## Custom Type Registration

The type registry allows you to encode/decode custom types that may not have native Rust equivalents:

```rust
use vuer_rpc::prelude::*;
use serde_json::json;

fn main() {
    // Register a custom datetime type
    GLOBAL_TYPE_REGISTRY.register(
        "datetime",
        |value| {
            // Encoder: JSON Value -> ZData
            Ok(ZData::new("datetime")
                .with_field("iso", value.clone()))
        },
        |zdata| {
            // Decoder: ZData -> JSON Value
            Ok(zdata.get_field("iso").unwrap().clone())
        },
        None, // Optional type checker
    );

    // Now the type will be automatically encoded/decoded
}
```

## ZData Encoding

ZData is a wrapper format for encoding types that don't have direct Rust equivalents (like NumPy arrays, PyTorch tensors, etc.):

```rust
use vuer_rpc::prelude::*;

// Create ZData for a custom type
let zdata = ZData::new("custom.Type")
    .with_binary(vec![1, 2, 3, 4])
    .with_dtype("uint8")
    .with_shape(vec![2, 2])
    .with_field("metadata", json!({"version": "1.0"}));

// Serialize to MessagePack
let bytes = serialize(&zdata)?;
```

### Built-in Type Support

With the `ndarray` feature:

```rust
use vuer_rpc::prelude::*;
use ndarray::Array;

#[cfg(feature = "ndarray")]
fn example() -> Result<()> {
    // Create a NumPy-compatible array
    let data = vec![1.0f32, 2.0, 3.0, 4.0];
    let array = Array::from_shape_vec([2, 2], data)?;
    let numpy_array = NumpyArray::new(array);

    // Convert to ZData
    let zdata = numpy_array.to_zdata()?;

    // Serialize
    let bytes = serialize(&zdata)?;

    Ok(())
}
```

With the `image` feature:

```rust
use vuer_rpc::prelude::*;
use image::{DynamicImage, ImageFormat};

#[cfg(feature = "image")]
fn example(img: DynamicImage) -> Result<()> {
    let image_data = ImageData::new(img, ImageFormat::Png);
    let zdata = image_data.to_zdata()?;
    let bytes = serialize(&zdata)?;
    Ok(())
}
```

## Type Conversion Fallbacks

When a type is not available in the Rust environment, VMP-RS provides helpful error messages:

```rust
use vuer_rpc::prelude::*;

// This will return an error if the 'ndarray' feature is not enabled
let result = decode_from_zdata::<NumpyArray<f32>>(&zdata);

match result {
    Ok(array) => println!("Successfully decoded array"),
    Err(VmpError::TypeConversion(msg)) => {
        // Error message suggests enabling the 'ndarray' feature
        eprintln!("Type not available: {}", msg);
    }
    _ => {}
}
```

## Cargo Features

- **`default`**: Includes `tokio` and `ndarray` features
- **`tokio`**: Async RPC manager with Tokio runtime
- **`ndarray`**: NumPy-compatible array support
- **`image`**: Image encoding/decoding support
- **`full`**: All features enabled

## Package Manager & Testing

### Modern Rust Tooling (2025)

This project uses the latest Rust tooling best practices:

- **Package Manager**: `cargo` (standard, built into Rust)
- **Test Runner**: `cargo test` (or use `cargo-nextest` for faster testing)
- **Build**: `cargo build --release` for optimized builds

### Running Tests

```bash
# Run all tests
cargo test

# Run with output
cargo test -- --nocapture

# Run specific test
cargo test test_basic_workflow

# With cargo-nextest (faster, better output)
cargo install cargo-nextest
cargo nextest run
```

### Building

```bash
# Debug build
cargo build

# Release build (optimized)
cargo build --release

# Check without building
cargo check

# Build documentation
cargo doc --open
```

## Known Limitations

### MessagePack + JSON Value Interop

When using `serde_json::Value` in message fields (data, value, args, kwargs), there are some limitations with MessagePack round-tripping:

- Simple values (strings, numbers, booleans) work well
- Complex nested objects may not round-trip perfectly
- For production use, consider using strongly-typed structs instead of `serde_json::Value`

**Workaround**: Define your message payloads as proper Rust structs:

```rust
#[derive(Serialize, Deserialize)]
struct MyPayload {
    x: i32,
    y: i32,
}

// Use with Message
let msg = Message::new("EVENT");
// Serialize your struct separately and include as needed
```

## Cross-Language Compatibility

VMP-RS is designed to be compatible with:

- **vmp-ts** (TypeScript/JavaScript)
- **vmp-py** (Python)
- **vmp-swift** (Swift, planned)
- **vmp-cpp** (C++, planned)

All implementations use MessagePack for serialization and follow the same ZData encoding conventions.

## Examples

See the [`examples/`](examples/) directory for complete working examples:

- `basic_messages.rs` - Creating and serializing messages
- `rpc_client.rs` - Async RPC client example
- `custom_types.rs` - Registering custom types
- `components.rs` - Working with Vuer component trees

## Documentation

- [API Documentation](https://docs.rs/vuer-rpc)
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
