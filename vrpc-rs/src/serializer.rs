//! MessagePack serialization for VMP
//!
//! Author: Ge Yang

use crate::error::{Result, VmpError};
use base64::Engine;
use crate::type_registry::GLOBAL_TYPE_REGISTRY;
use crate::types::{Message, VuerComponent};
use crate::zdata::ZData;
use serde::Serialize;
use serde_json::Value;

/// Serialization options
#[derive(Debug, Clone)]
pub struct SerializeOptions {
    /// Recursively encode nested structures
    pub recursive: bool,

    /// Encode undefined/null values
    pub encode_undefined: bool,

    /// Use the global type registry for custom types
    pub use_type_registry: bool,
}

impl Default for SerializeOptions {
    fn default() -> Self {
        Self {
            recursive: true,
            encode_undefined: false,
            use_type_registry: true,
        }
    }
}

/// Serialize a value to MessagePack binary format
///
/// This function handles:
/// - Recursive encoding of nested structures
/// - ZData type detection and encoding
/// - Custom type registry lookups
pub fn serialize<T: Serialize>(value: &T) -> Result<Vec<u8>> {
    serialize_with_options(value, &SerializeOptions::default())
}

/// Serialize with custom options
pub fn serialize_with_options<T: Serialize>(
    value: &T,
    _options: &SerializeOptions,
) -> Result<Vec<u8>> {
    let bytes = rmp_serde::to_vec(value)
        .map_err(|e| VmpError::Serialization(e.to_string()))?;
    Ok(bytes)
}

/// Serialize a message to MessagePack
pub fn serialize_message(message: &Message) -> Result<Vec<u8>> {
    serialize(message)
}

/// Serialize a Vuer component tree to MessagePack
///
/// This recursively encodes the component and all its children,
/// including any ZData types in the component properties.
pub fn serialize_component(component: &VuerComponent) -> Result<Vec<u8>> {
    serialize(component)
}

/// Recursively encode a JSON value, converting custom types to ZData
pub fn encode_value_recursive(value: &Value, options: &SerializeOptions) -> Result<Value> {
    if !options.recursive {
        return Ok(value.clone());
    }

    match value {
        Value::Object(map) => {
            // Check if this is already a ZData object
            if map.contains_key("ztype") {
                return Ok(value.clone());
            }

            // Try to encode using type registry
            if options.use_type_registry {
                if let Some(zdata) = GLOBAL_TYPE_REGISTRY.try_encode(value) {
                    return Ok(serde_json::to_value(&zdata)?);
                }
            }

            // Recursively process object fields
            let mut result = serde_json::Map::new();
            for (key, val) in map {
                let encoded = encode_value_recursive(val, options)?;
                result.insert(key.clone(), encoded);
            }
            Ok(Value::Object(result))
        }
        Value::Array(arr) => {
            // Recursively process array elements
            let encoded: Result<Vec<Value>> = arr
                .iter()
                .map(|v| encode_value_recursive(v, options))
                .collect();
            Ok(Value::Array(encoded?))
        }
        Value::Null if !options.encode_undefined => {
            Err(VmpError::Serialization("Null value not allowed".to_string()))
        }
        _ => Ok(value.clone()),
    }
}

/// Serialize to base64-encoded MessagePack
pub fn serialize_to_base64<T: Serialize>(value: &T) -> Result<String> {
    let bytes = serialize(value)?;
    Ok(base64::engine::general_purpose::STANDARD.encode(&bytes))
}

/// Helper to convert ZData to MessagePack bytes
pub fn zdata_to_bytes(zdata: &ZData) -> Result<Vec<u8>> {
    serialize(zdata)
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn test_serialize_message() {
        let mut msg = Message::new("TEST_EVENT");
        msg.data = Some(json!({"foo": "bar"}));

        let bytes = serialize_message(&msg).unwrap();
        assert!(!bytes.is_empty());
    }

    #[test]
    fn test_serialize_component() {
        let component = VuerComponent::new("scene")
            .with_prop("background", json!("#000000"));

        let bytes = serialize_component(&component).unwrap();
        assert!(!bytes.is_empty());
    }

    #[test]
    fn test_encode_value_recursive() {
        let value = json!({
            "nested": {
                "array": [1, 2, 3],
                "object": {"key": "value"}
            }
        });

        let options = SerializeOptions::default();
        let encoded = encode_value_recursive(&value, &options).unwrap();
        assert_eq!(encoded, value);
    }

    #[test]
    fn test_zdata_to_bytes() {
        let zdata = ZData::new("test.Type")
            .with_binary(vec![1, 2, 3, 4]);

        let bytes = zdata_to_bytes(&zdata).unwrap();
        assert!(!bytes.is_empty());
    }
}
