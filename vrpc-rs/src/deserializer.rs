//! MessagePack deserialization for VMP
//!
//! Author: Ge Yang

use crate::error::{Result, VmpError};
use base64::Engine;
use crate::type_registry::GLOBAL_TYPE_REGISTRY;
use crate::types::{Message, VuerComponent};
use crate::zdata::ZData;
use serde::de::DeserializeOwned;
use serde_json::Value;

/// Deserialization options
#[derive(Debug, Clone)]
pub struct DeserializeOptions {
    /// Recursively decode nested ZData structures
    pub recursive: bool,

    /// Validate message structure
    pub validate: bool,

    /// Use the global type registry for custom types
    pub use_type_registry: bool,
}

impl Default for DeserializeOptions {
    fn default() -> Self {
        Self {
            recursive: true,
            validate: true,
            use_type_registry: true,
        }
    }
}

/// Deserialize from MessagePack binary format
pub fn deserialize<T: DeserializeOwned>(bytes: &[u8]) -> Result<T> {
    deserialize_with_options(bytes, &DeserializeOptions::default())
}

/// Deserialize with custom options
pub fn deserialize_with_options<T: DeserializeOwned>(
    bytes: &[u8],
    _options: &DeserializeOptions,
) -> Result<T> {
    let value = rmp_serde::from_slice(bytes)
        .map_err(|e| VmpError::Deserialization(e.to_string()))?;
    Ok(value)
}

/// Deserialize a message from MessagePack
pub fn deserialize_message(bytes: &[u8]) -> Result<Message> {
    deserialize(bytes)
}

/// Deserialize a Vuer component from MessagePack
pub fn deserialize_component(bytes: &[u8]) -> Result<VuerComponent> {
    deserialize(bytes)
}

/// Recursively decode a JSON value, converting ZData objects
pub fn decode_value_recursive(value: &Value, options: &DeserializeOptions) -> Result<Value> {
    if !options.recursive {
        return Ok(value.clone());
    }

    match value {
        Value::Object(map) => {
            // Check if this is a ZData object
            if map.contains_key("ztype") {
                let zdata: ZData = serde_json::from_value(value.clone())?;

                // Try to decode using type registry
                if options.use_type_registry && GLOBAL_TYPE_REGISTRY.is_registered(&zdata.ztype) {
                    return GLOBAL_TYPE_REGISTRY.decode(&zdata);
                }

                // Return as-is if not registered
                return Ok(value.clone());
            }

            // Recursively process object fields
            let mut result = serde_json::Map::new();
            for (key, val) in map {
                let decoded = decode_value_recursive(val, options)?;
                result.insert(key.clone(), decoded);
            }
            Ok(Value::Object(result))
        }
        Value::Array(arr) => {
            // Recursively process array elements
            let decoded: Result<Vec<Value>> = arr
                .iter()
                .map(|v| decode_value_recursive(v, options))
                .collect();
            Ok(Value::Array(decoded?))
        }
        _ => Ok(value.clone()),
    }
}

/// Deserialize from base64-encoded MessagePack
pub fn deserialize_from_base64<T: DeserializeOwned>(encoded: &str) -> Result<T> {
    let bytes = base64::engine::general_purpose::STANDARD
        .decode(encoded)
        .map_err(|e| VmpError::Deserialization(format!("Base64 decode error: {}", e)))?;
    deserialize(&bytes)
}

/// Helper to convert MessagePack bytes to ZData
pub fn bytes_to_zdata(bytes: &[u8]) -> Result<ZData> {
    deserialize(bytes)
}

/// Validate message structure
pub fn validate_message(msg: &Message) -> Result<()> {
    if msg.etype.is_empty() {
        return Err(VmpError::InvalidMessage(
            "Message etype cannot be empty".to_string(),
        ));
    }

    // RPC requests must have rtype
    if msg.args.is_some() || msg.kwargs.is_some() {
        if msg.rtype.is_none() {
            return Err(VmpError::InvalidMessage(
                "RPC request must have rtype field".to_string(),
            ));
        }
    }

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::serializer::serialize_message;
    use serde_json::json;

    #[test]
    fn test_deserialize_message() {
        let msg = Message::new("TEST_EVENT")
            .with_data(json!("test value"));

        let bytes = serialize_message(&msg).unwrap();
        let deserialized: Message = deserialize_message(&bytes).unwrap();

        assert_eq!(msg.etype, deserialized.etype);
        assert_eq!(msg.ts, deserialized.ts);
        // JSON Value roundtrip through MessagePack has known limitations
    }

    #[test]
    fn test_roundtrip_component() {
        let component = VuerComponent::new("scene")
            .with_prop("background", json!("#000000"));

        let bytes = crate::serializer::serialize_component(&component).unwrap();
        let deserialized = deserialize_component(&bytes).unwrap();

        assert_eq!(component, deserialized);
    }

    #[test]
    fn test_validate_message() {
        let valid_msg = Message::new("TEST");
        assert!(validate_message(&valid_msg).is_ok());

        let mut invalid_msg = Message::new("");
        assert!(validate_message(&invalid_msg).is_err());

        invalid_msg.etype = "TEST".to_string();
        invalid_msg.args = Some(vec![]);
        // Missing rtype for RPC
        assert!(validate_message(&invalid_msg).is_err());
    }

    #[test]
    fn test_decode_value_recursive() {
        let value = json!({
            "nested": {
                "array": [1, 2, 3],
                "object": {"key": "value"}
            }
        });

        let options = DeserializeOptions::default();
        let decoded = decode_value_recursive(&value, &options).unwrap();
        assert_eq!(decoded, value);
    }
}
