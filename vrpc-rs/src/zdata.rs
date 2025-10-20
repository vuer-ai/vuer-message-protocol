//! ZData encoding system for custom types
//!
//! Author: Ge Yang

use crate::error::{Result, VmpError};
use indexmap::IndexMap;
use serde::{Deserialize, Serialize};
use serde_json::Value;

/// ZData wrapper format for custom data types
///
/// This struct provides a generic container for encoding custom types
/// that may not have native Rust equivalents. It uses a type discriminator
/// (`ztype`) and flexible fields to support various data formats.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct ZData {
    /// Type identifier (e.g., "numpy.ndarray", "torch.Tensor", "image")
    pub ztype: String,

    /// Binary data (for arrays, images, etc.)
    #[serde(skip_serializing_if = "Option::is_none")]
    #[serde(with = "serde_bytes")]
    pub b: Option<Vec<u8>>,

    /// Element data type (for arrays/tensors)
    #[serde(skip_serializing_if = "Option::is_none")]
    pub dtype: Option<String>,

    /// Shape dimensions (for arrays/tensors)
    #[serde(skip_serializing_if = "Option::is_none")]
    pub shape: Option<Vec<usize>>,

    /// Additional fields for custom types
    #[serde(flatten)]
    pub extra: IndexMap<String, Value>,
}

impl ZData {
    /// Create a new ZData with the given type identifier
    pub fn new(ztype: impl Into<String>) -> Self {
        Self {
            ztype: ztype.into(),
            b: None,
            dtype: None,
            shape: None,
            extra: IndexMap::new(),
        }
    }

    /// Set binary data
    pub fn with_binary(mut self, data: Vec<u8>) -> Self {
        self.b = Some(data);
        self
    }

    /// Set data type
    pub fn with_dtype(mut self, dtype: impl Into<String>) -> Self {
        self.dtype = Some(dtype.into());
        self
    }

    /// Set shape
    pub fn with_shape(mut self, shape: Vec<usize>) -> Self {
        self.shape = Some(shape);
        self
    }

    /// Add an extra field
    pub fn with_field(mut self, key: impl Into<String>, value: Value) -> Self {
        self.extra.insert(key.into(), value);
        self
    }

    /// Get an extra field
    pub fn get_field(&self, key: &str) -> Option<&Value> {
        self.extra.get(key)
    }

    /// Check if this is a specific type
    pub fn is_type(&self, ztype: &str) -> bool {
        self.ztype == ztype
    }
}

/// Type conversion trait for custom types
///
/// This trait allows types to be encoded/decoded to/from ZData format.
/// It provides a fallback mechanism for types that may not be available
/// in the Rust environment.
pub trait ZDataConversion: Sized {
    /// The type identifier for this type
    fn ztype() -> &'static str;

    /// Encode this value to ZData format
    fn to_zdata(&self) -> Result<ZData>;

    /// Decode from ZData format
    ///
    /// If the type is not available in the current environment,
    /// this should return a TypeConversion error with a helpful message.
    fn from_zdata(zdata: &ZData) -> Result<Self>;

    /// Check if this type is available in the current environment
    ///
    /// Returns true if the type can be encoded/decoded, false otherwise.
    /// This allows graceful degradation when optional dependencies are missing.
    fn is_available() -> bool {
        true
    }
}

/// Fallback type for when a ZData type is not available
///
/// This allows the system to preserve unknown types without failing.
/// The original ZData is stored and can be passed through without modification.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct UnknownType {
    pub zdata: ZData,
}

impl UnknownType {
    /// Create a new unknown type from ZData
    pub fn new(zdata: ZData) -> Self {
        Self { zdata }
    }

    /// Get the type identifier
    pub fn ztype(&self) -> &str {
        &self.zdata.ztype
    }

    /// Get the underlying ZData
    pub fn as_zdata(&self) -> &ZData {
        &self.zdata
    }
}

/// Helper function to encode a value to ZData if it implements the trait
pub fn encode_to_zdata<T: ZDataConversion>(value: &T) -> Result<ZData> {
    if !T::is_available() {
        return Err(VmpError::TypeConversion(format!(
            "Type '{}' is not available in this environment. \
             Consider enabling the appropriate feature flag.",
            T::ztype()
        )));
    }
    value.to_zdata()
}

/// Helper function to decode ZData to a specific type
pub fn decode_from_zdata<T: ZDataConversion>(zdata: &ZData) -> Result<T> {
    if !T::is_available() {
        return Err(VmpError::TypeConversion(format!(
            "Type '{}' is not available in this environment. \
             Consider enabling the appropriate feature flag.",
            T::ztype()
        )));
    }
    T::from_zdata(zdata)
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn test_zdata_creation() {
        let zdata = ZData::new("test.Type")
            .with_binary(vec![1, 2, 3, 4])
            .with_dtype("float32")
            .with_shape(vec![2, 2])
            .with_field("custom", json!("value"));

        assert_eq!(zdata.ztype, "test.Type");
        assert_eq!(zdata.b, Some(vec![1, 2, 3, 4]));
        assert_eq!(zdata.dtype, Some("float32".to_string()));
        assert_eq!(zdata.shape, Some(vec![2, 2]));
        assert_eq!(zdata.get_field("custom"), Some(&json!("value")));
    }

    #[test]
    fn test_unknown_type() {
        let zdata = ZData::new("unknown.Type");
        let unknown = UnknownType::new(zdata.clone());

        assert_eq!(unknown.ztype(), "unknown.Type");
        assert_eq!(unknown.as_zdata(), &zdata);
    }

    #[test]
    fn test_zdata_serialization() {
        let zdata = ZData::new("numpy.ndarray")
            .with_binary(vec![0, 1, 2, 3])
            .with_dtype("uint8")
            .with_shape(vec![2, 2]);

        let json = serde_json::to_string(&zdata).unwrap();
        let deserialized: ZData = serde_json::from_str(&json).unwrap();

        assert_eq!(zdata, deserialized);
    }
}
