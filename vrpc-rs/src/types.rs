//! Core type definitions for VMP
//!
//! Author: Ge Yang

use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Timestamp in milliseconds since Unix epoch
pub type Timestamp = i64;

/// Generic message envelope with all possible fields
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(default)]
pub struct Message {
    /// Timestamp in milliseconds
    pub ts: Timestamp,

    /// Event type or queue name
    pub etype: String,

    /// Response type (RPC only)
    #[serde(skip_serializing_if = "Option::is_none")]
    pub rtype: Option<String>,

    /// Positional arguments (RPC)
    #[serde(skip_serializing_if = "Option::is_none")]
    pub args: Option<Vec<serde_json::Value>>,

    /// Keyword arguments (RPC)
    #[serde(skip_serializing_if = "Option::is_none")]
    pub kwargs: Option<HashMap<String, serde_json::Value>>,

    /// Server payload
    #[serde(skip_serializing_if = "Option::is_none")]
    pub data: Option<serde_json::Value>,

    /// Client payload
    #[serde(skip_serializing_if = "Option::is_none")]
    pub value: Option<serde_json::Value>,
}

/// Client-to-server event (uses value for payload)
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(default)]
pub struct ClientEvent {
    /// Timestamp in milliseconds
    pub ts: Timestamp,

    /// Event type
    pub etype: String,

    /// Response type (for RPC requests)
    #[serde(skip_serializing_if = "Option::is_none")]
    pub rtype: Option<String>,

    /// Client payload
    pub value: serde_json::Value,
}

/// Server-to-client event (uses data for payload)
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(default)]
pub struct ServerEvent {
    /// Timestamp in milliseconds
    pub ts: Timestamp,

    /// Event type
    pub etype: String,

    /// Server payload
    pub data: serde_json::Value,
}

/// RPC Request (includes rtype for response routing)
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(default)]
pub struct RpcRequest {
    /// Timestamp in milliseconds
    pub ts: Timestamp,

    /// Event type (method name)
    pub etype: String,

    /// Response type (required for RPC)
    pub rtype: String,

    /// Positional arguments
    #[serde(skip_serializing_if = "Option::is_none")]
    pub args: Option<Vec<serde_json::Value>>,

    /// Keyword arguments
    #[serde(skip_serializing_if = "Option::is_none")]
    pub kwargs: Option<HashMap<String, serde_json::Value>>,
}

/// RPC Response
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(default)]
pub struct RpcResponse {
    /// Timestamp in milliseconds
    pub ts: Timestamp,

    /// Event type (matches request's rtype)
    pub etype: String,

    /// Response payload (server)
    #[serde(skip_serializing_if = "Option::is_none")]
    pub data: Option<serde_json::Value>,

    /// Response payload (client)
    #[serde(skip_serializing_if = "Option::is_none")]
    pub value: Option<serde_json::Value>,

    /// Success flag
    #[serde(skip_serializing_if = "Option::is_none")]
    pub ok: Option<bool>,

    /// Error message
    #[serde(skip_serializing_if = "Option::is_none")]
    pub error: Option<String>,
}

/// Vuer component schema (nested structure)
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(default)]
pub struct VuerComponent {
    /// Component type
    pub tag: String,

    /// Nested components
    #[serde(skip_serializing_if = "Option::is_none")]
    pub children: Option<Vec<VuerComponent>>,

    /// Additional properties stored as dynamic values
    #[serde(flatten)]
    pub props: HashMap<String, serde_json::Value>,
}

impl Default for Message {
    fn default() -> Self {
        Self {
            ts: 0,
            etype: String::new(),
            rtype: None,
            args: None,
            kwargs: None,
            data: None,
            value: None,
        }
    }
}

impl Message {
    /// Create a new message with the current timestamp
    pub fn new(etype: impl Into<String>) -> Self {
        Self {
            ts: chrono::Utc::now().timestamp_millis(),
            etype: etype.into(),
            rtype: None,
            args: None,
            kwargs: None,
            data: None,
            value: None,
        }
    }

    /// Set the response type for RPC
    pub fn with_rtype(mut self, rtype: impl Into<String>) -> Self {
        self.rtype = Some(rtype.into());
        self
    }

    /// Set the data payload
    pub fn with_data(mut self, data: serde_json::Value) -> Self {
        self.data = Some(data);
        self
    }

    /// Set the value payload
    pub fn with_value(mut self, value: serde_json::Value) -> Self {
        self.value = Some(value);
        self
    }
}

impl Default for ClientEvent {
    fn default() -> Self {
        Self {
            ts: 0,
            etype: String::new(),
            rtype: None,
            value: serde_json::Value::Null,
        }
    }
}

impl ClientEvent {
    /// Create a new client event with the current timestamp
    pub fn new(etype: impl Into<String>, value: serde_json::Value) -> Self {
        Self {
            ts: chrono::Utc::now().timestamp_millis(),
            etype: etype.into(),
            rtype: None,
            value,
        }
    }

    /// Set the response type for RPC
    pub fn with_rtype(mut self, rtype: impl Into<String>) -> Self {
        self.rtype = Some(rtype.into());
        self
    }
}

impl Default for ServerEvent {
    fn default() -> Self {
        Self {
            ts: 0,
            etype: String::new(),
            data: serde_json::Value::Null,
        }
    }
}

impl ServerEvent {
    /// Create a new server event with the current timestamp
    pub fn new(etype: impl Into<String>, data: serde_json::Value) -> Self {
        Self {
            ts: chrono::Utc::now().timestamp_millis(),
            etype: etype.into(),
            data,
        }
    }
}

impl Default for RpcRequest {
    fn default() -> Self {
        Self {
            ts: 0,
            etype: String::new(),
            rtype: String::new(),
            args: None,
            kwargs: None,
        }
    }
}

impl RpcRequest {
    /// Create a new RPC request with the current timestamp
    pub fn new(etype: impl Into<String>, rtype: impl Into<String>) -> Self {
        Self {
            ts: chrono::Utc::now().timestamp_millis(),
            etype: etype.into(),
            rtype: rtype.into(),
            args: None,
            kwargs: None,
        }
    }

    /// Set positional arguments
    pub fn with_args(mut self, args: Vec<serde_json::Value>) -> Self {
        self.args = Some(args);
        self
    }

    /// Set keyword arguments
    pub fn with_kwargs(mut self, kwargs: HashMap<String, serde_json::Value>) -> Self {
        self.kwargs = Some(kwargs);
        self
    }
}

impl Default for RpcResponse {
    fn default() -> Self {
        Self {
            ts: 0,
            etype: String::new(),
            data: None,
            value: None,
            ok: None,
            error: None,
        }
    }
}

impl RpcResponse {
    /// Create a successful RPC response
    pub fn success(etype: impl Into<String>, data: serde_json::Value) -> Self {
        Self {
            ts: chrono::Utc::now().timestamp_millis(),
            etype: etype.into(),
            data: Some(data),
            value: None,
            ok: Some(true),
            error: None,
        }
    }

    /// Create a failed RPC response
    pub fn error(etype: impl Into<String>, error: impl Into<String>) -> Self {
        Self {
            ts: chrono::Utc::now().timestamp_millis(),
            etype: etype.into(),
            data: None,
            value: None,
            ok: Some(false),
            error: Some(error.into()),
        }
    }
}

impl Default for VuerComponent {
    fn default() -> Self {
        Self {
            tag: String::new(),
            children: None,
            props: HashMap::new(),
        }
    }
}

impl VuerComponent {
    /// Create a new component with the given tag
    pub fn new(tag: impl Into<String>) -> Self {
        Self {
            tag: tag.into(),
            children: None,
            props: HashMap::new(),
        }
    }

    /// Add a child component
    pub fn with_child(mut self, child: VuerComponent) -> Self {
        self.children.get_or_insert_with(Vec::new).push(child);
        self
    }

    /// Set a property
    pub fn with_prop(mut self, key: impl Into<String>, value: serde_json::Value) -> Self {
        self.props.insert(key.into(), value);
        self
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn test_message_creation() {
        let msg = Message::new("TEST_EVENT")
            .with_data(json!({"foo": "bar"}));

        assert_eq!(msg.etype, "TEST_EVENT");
        assert!(msg.data.is_some());
        assert!(msg.ts > 0);
    }

    #[test]
    fn test_client_event() {
        let event = ClientEvent::new("CLICK", json!({"x": 100, "y": 200}));
        assert_eq!(event.etype, "CLICK");
        assert_eq!(event.value["x"], 100);
    }

    #[test]
    fn test_rpc_request() {
        let mut kwargs = HashMap::new();
        kwargs.insert("seed".to_string(), json!(100));

        let req = RpcRequest::new("render", "rpc-123")
            .with_kwargs(kwargs);

        assert_eq!(req.etype, "render");
        assert_eq!(req.rtype, "rpc-123");
    }

    #[test]
    fn test_vuer_component() {
        let child = VuerComponent::new("sphere")
            .with_prop("radius", json!(1.0));

        let component = VuerComponent::new("scene")
            .with_child(child)
            .with_prop("background", json!("#000000"));

        assert_eq!(component.tag, "scene");
        assert_eq!(component.children.as_ref().unwrap().len(), 1);
    }
}
