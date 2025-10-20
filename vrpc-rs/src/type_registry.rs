//! Type registry for custom ZData types
//!
//! Author: Ge Yang

use crate::error::{Result, VmpError};
use crate::zdata::ZData;
use serde_json::Value;
use std::collections::HashMap;
use std::sync::{Arc, RwLock};

/// Encoder function type: converts a JSON value to ZData
pub type EncoderFn = Arc<dyn Fn(&Value) -> Result<ZData> + Send + Sync>;

/// Decoder function type: converts ZData to a JSON value
pub type DecoderFn = Arc<dyn Fn(&ZData) -> Result<Value> + Send + Sync>;

/// Type checker function: checks if a value is of this type
pub type TypeCheckerFn = Arc<dyn Fn(&Value) -> bool + Send + Sync>;

/// Registration information for a custom type
#[derive(Clone)]
pub struct TypeRegistration {
    /// Type identifier (e.g., "datetime", "numpy.ndarray")
    pub ztype: String,

    /// Encoder function
    pub encoder: EncoderFn,

    /// Decoder function
    pub decoder: DecoderFn,

    /// Type checker (optional)
    pub type_checker: Option<TypeCheckerFn>,
}

/// Global type registry for custom ZData types
///
/// This allows users to register custom encoders/decoders for types
/// that may not have native Rust equivalents.
#[derive(Clone)]
pub struct TypeRegistry {
    types: Arc<RwLock<HashMap<String, TypeRegistration>>>,
}

impl Default for TypeRegistry {
    fn default() -> Self {
        Self::new()
    }
}

impl TypeRegistry {
    /// Create a new empty type registry
    pub fn new() -> Self {
        Self {
            types: Arc::new(RwLock::new(HashMap::new())),
        }
    }

    /// Register a custom type with encoder and decoder functions
    ///
    /// # Example
    ///
    /// ```rust,ignore
    /// use serde_json::json;
    ///
    /// registry.register(
    ///     "datetime",
    ///     |value| {
    ///         // Encode datetime to ZData
    ///         Ok(ZData::new("datetime")
    ///             .with_field("iso", value.clone()))
    ///     },
    ///     |zdata| {
    ///         // Decode ZData to datetime value
    ///         Ok(zdata.get_field("iso").unwrap().clone())
    ///     },
    ///     None,
    /// );
    /// ```
    pub fn register<E, D>(
        &self,
        ztype: impl Into<String>,
        encoder: E,
        decoder: D,
        type_checker: Option<TypeCheckerFn>,
    ) where
        E: Fn(&Value) -> Result<ZData> + Send + Sync + 'static,
        D: Fn(&ZData) -> Result<Value> + Send + Sync + 'static,
    {
        let ztype = ztype.into();
        let registration = TypeRegistration {
            ztype: ztype.clone(),
            encoder: Arc::new(encoder),
            decoder: Arc::new(decoder),
            type_checker,
        };

        let mut types = self.types.write().unwrap();
        types.insert(ztype, registration);
    }

    /// Encode a value using a registered type
    pub fn encode(&self, ztype: &str, value: &Value) -> Result<ZData> {
        let types = self.types.read().unwrap();
        let registration = types
            .get(ztype)
            .ok_or_else(|| VmpError::TypeNotRegistered(ztype.to_string()))?;

        (registration.encoder)(value)
    }

    /// Decode ZData using a registered type
    pub fn decode(&self, zdata: &ZData) -> Result<Value> {
        let types = self.types.read().unwrap();
        let registration = types
            .get(&zdata.ztype)
            .ok_or_else(|| VmpError::TypeNotRegistered(zdata.ztype.clone()))?;

        (registration.decoder)(zdata)
    }

    /// Check if a type is registered
    pub fn is_registered(&self, ztype: &str) -> bool {
        let types = self.types.read().unwrap();
        types.contains_key(ztype)
    }

    /// Try to encode a value by checking all registered type checkers
    pub fn try_encode(&self, value: &Value) -> Option<ZData> {
        let types = self.types.read().unwrap();

        for registration in types.values() {
            if let Some(checker) = &registration.type_checker {
                if checker(value) {
                    if let Ok(zdata) = (registration.encoder)(value) {
                        return Some(zdata);
                    }
                }
            }
        }

        None
    }

    /// Get all registered type names
    pub fn registered_types(&self) -> Vec<String> {
        let types = self.types.read().unwrap();
        types.keys().cloned().collect()
    }
}

lazy_static::lazy_static! {
    /// Global type registry instance
    pub static ref GLOBAL_TYPE_REGISTRY: TypeRegistry = TypeRegistry::new();
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn test_type_registration() {
        let registry = TypeRegistry::new();

        registry.register(
            "test.Type",
            |value| {
                Ok(ZData::new("test.Type")
                    .with_field("value", value.clone()))
            },
            |zdata| {
                Ok(zdata.get_field("value").unwrap().clone())
            },
            None,
        );

        assert!(registry.is_registered("test.Type"));
        assert!(!registry.is_registered("unknown.Type"));
    }

    #[test]
    fn test_encode_decode() {
        let registry = TypeRegistry::new();

        registry.register(
            "datetime",
            |value| {
                Ok(ZData::new("datetime")
                    .with_field("iso", value.clone()))
            },
            |zdata| {
                Ok(zdata.get_field("iso").unwrap().clone())
            },
            None,
        );

        let value = json!("2025-01-20T12:00:00Z");
        let zdata = registry.encode("datetime", &value).unwrap();
        let decoded = registry.decode(&zdata).unwrap();

        assert_eq!(value, decoded);
    }

    #[test]
    fn test_type_checker() {
        let registry = TypeRegistry::new();

        registry.register(
            "number",
            |value| {
                Ok(ZData::new("number")
                    .with_field("n", value.clone()))
            },
            |zdata| {
                Ok(zdata.get_field("n").unwrap().clone())
            },
            Some(Arc::new(|v| v.is_number())),
        );

        let number = json!(42);
        let string = json!("not a number");

        assert!(registry.try_encode(&number).is_some());
        assert!(registry.try_encode(&string).is_none());
    }
}
