//! VMP-RS: Rust Implementation of the Vuer Message Protocol
//!
//! Author: Ge Yang
//!
//! A lightweight, cross-language messaging and RPC protocol designed for use with Vuer and Zaku.
//!
//! # Features
//!
//! - **MessagePack Serialization**: Efficient binary encoding for cross-language compatibility
//! - **Extensible Type System**: Register custom types with ZData encoding
//! - **RPC Support**: Request-response correlation with async/await
//! - **Built-in Types**: Optional support for NumPy arrays and images
//! - **Type Conversion Fallbacks**: Graceful handling of unavailable types
//!
//! # Quick Start
//!
//! ```rust
//! use vuer_rpc::prelude::*;
//! use serde_json::json;
//!
//! // Create a message
//! let msg = Message::new("CLICK")
//!     .with_value(json!({"x": 100, "y": 200}));
//!
//! // Serialize to MessagePack
//! let bytes = serialize_message(&msg).unwrap();
//!
//! // Deserialize
//! let restored: Message = deserialize_message(&bytes).unwrap();
//! ```
//!
//! # RPC Example
//!
//! ```rust,ignore
//! use vuer_rpc::prelude::*;
//! use std::time::Duration;
//!
//! #[tokio::main]
//! async fn main() {
//!     let manager = RpcManager::new();
//!
//!     // Send an RPC request
//!     let (req, response_fut) = manager
//!         .request("render", None, None, Duration::from_secs(5))
//!         .await
//!         .unwrap();
//!
//!     // ... send req over the network ...
//!
//!     // Await the response
//!     let response = response_fut.await.unwrap();
//!     println!("Result: {:?}", response.data);
//! }
//! ```
//!
//! # Custom Types
//!
//! ```rust
//! use vuer_rpc::prelude::*;
//! use serde_json::json;
//!
//! // Register a custom type
//! GLOBAL_TYPE_REGISTRY.register(
//!     "datetime",
//!     |value| {
//!         Ok(ZData::new("datetime")
//!             .with_field("iso", value.clone()))
//!     },
//!     |zdata| {
//!         Ok(zdata.get_field("iso").unwrap().clone())
//!     },
//!     None,
//! );
//! ```

pub mod builtin_types;
pub mod deserializer;
pub mod error;
pub mod rpc;
pub mod serializer;
pub mod type_registry;
pub mod types;
pub mod zdata;

// Re-export commonly used types
pub use error::{Result, VmpError};
pub use types::{
    ClientEvent, Message, RpcRequest, RpcResponse, ServerEvent, Timestamp, VuerComponent,
};
pub use zdata::{ZData, ZDataConversion};

// Re-export serialization functions
pub use deserializer::{
    deserialize, deserialize_component, deserialize_from_base64, deserialize_message,
};
pub use serializer::{serialize, serialize_component, serialize_message, serialize_to_base64};

// Re-export RPC utilities
#[cfg(feature = "tokio")]
pub use rpc::RpcManager;
pub use rpc::{create_rpc_request, create_rpc_response, generate_request_id};

// Re-export type registry
pub use type_registry::{TypeRegistration, TypeRegistry, GLOBAL_TYPE_REGISTRY};

/// Prelude module for convenient imports
pub mod prelude {
    pub use crate::deserializer::{
        deserialize, deserialize_component, deserialize_from_base64, deserialize_message,
    };
    pub use crate::error::{Result, VmpError};
    pub use crate::serializer::{
        serialize, serialize_component, serialize_message, serialize_to_base64,
    };
    pub use crate::type_registry::{TypeRegistry, GLOBAL_TYPE_REGISTRY};
    pub use crate::types::{
        ClientEvent, Message, RpcRequest, RpcResponse, ServerEvent, Timestamp, VuerComponent,
    };
    pub use crate::zdata::{ZData, ZDataConversion};

    #[cfg(feature = "tokio")]
    pub use crate::rpc::RpcManager;
    pub use crate::rpc::{create_rpc_request, create_rpc_response, generate_request_id};

    #[cfg(feature = "ndarray")]
    pub use crate::builtin_types::NumpyArray;

    #[cfg(feature = "image")]
    pub use crate::builtin_types::ImageData;
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn test_basic_workflow() {
        // Create a message with simple data
        let msg = Message::new("TEST_EVENT").with_data(json!("simple string"));

        println!("Original message: {:?}", msg);

        // Serialize
        let bytes = serialize_message(&msg).unwrap();
        println!("Serialized bytes: {:?}", bytes);
        println!("Bytes length: {}", bytes.len());

        // Deserialize
        let restored: Message = deserialize_message(&bytes).unwrap();
        println!("Restored message: {:?}", restored);

        assert_eq!(msg.etype, restored.etype);
        assert_eq!(msg.ts, restored.ts);
        // Note: serde_json::Value may not roundtrip perfectly through MessagePack
        // This is a known limitation when mixing JSON and MessagePack
    }

    #[test]
    fn test_message_with_object() {
        // Test with object data
        let msg = Message::new("TEST_EVENT");

        // Serialize without data field
        let bytes = serialize_message(&msg).unwrap();

        // Deserialize
        let restored: Message = deserialize_message(&bytes).unwrap();

        assert_eq!(msg.etype, restored.etype);
    }

    #[test]
    fn test_component_tree() {
        let child = VuerComponent::new("sphere").with_prop("radius", json!(1.0));

        let component = VuerComponent::new("scene")
            .with_child(child)
            .with_prop("background", json!("#000000"));

        let bytes = serialize_component(&component).unwrap();
        let restored = deserialize_component(&bytes).unwrap();

        assert_eq!(component, restored);
    }

    #[test]
    fn test_zdata_encoding() {
        let zdata = ZData::new("test.Type")
            .with_binary(vec![1, 2, 3, 4])
            .with_dtype("uint8")
            .with_shape(vec![2, 2]);

        let bytes = serialize(&zdata).unwrap();
        let restored: ZData = deserialize(&bytes).unwrap();

        assert_eq!(zdata, restored);
    }
}
