//! RPC (Remote Procedure Call) utilities
//!
//! Author: Ge Yang

use crate::error::{Result, VmpError};
use crate::types::{RpcRequest, RpcResponse};
use serde_json::Value;
use std::collections::HashMap;
use std::time::Duration;
use uuid::Uuid;

#[cfg(feature = "tokio")]
use tokio::sync::oneshot;
#[cfg(feature = "tokio")]
use tokio::time::timeout;

/// Generate a unique request ID
pub fn generate_request_id() -> String {
    format!("rpc-{}", Uuid::new_v4())
}

/// Create an RPC request
pub fn create_rpc_request(
    etype: impl Into<String>,
    args: Option<Vec<Value>>,
    kwargs: Option<HashMap<String, Value>>,
) -> RpcRequest {
    let rtype = generate_request_id();
    let mut req = RpcRequest::new(etype, rtype);
    if let Some(a) = args {
        req = req.with_args(a);
    }
    if let Some(k) = kwargs {
        req = req.with_kwargs(k);
    }
    req
}

/// Create an RPC response
pub fn create_rpc_response(
    etype: impl Into<String>,
    result: Result<Value>,
) -> RpcResponse {
    match result {
        Ok(data) => RpcResponse::success(etype, data),
        Err(e) => RpcResponse::error(etype, e.to_string()),
    }
}

#[cfg(feature = "tokio")]
type ResponseSender = oneshot::Sender<RpcResponse>;

/// RPC Manager for handling request-response correlation
///
/// This manager maintains a registry of pending RPC requests and
/// correlates responses back to the original callers using async channels.
#[cfg(feature = "tokio")]
#[derive(Clone)]
pub struct RpcManager {
    pending: std::sync::Arc<tokio::sync::Mutex<HashMap<String, ResponseSender>>>,
}

#[cfg(feature = "tokio")]
impl Default for RpcManager {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(feature = "tokio")]
impl RpcManager {
    /// Create a new RPC manager
    pub fn new() -> Self {
        Self {
            pending: std::sync::Arc::new(tokio::sync::Mutex::new(HashMap::new())),
        }
    }

    /// Send an RPC request and wait for a response
    ///
    /// This method creates a request with a unique ID, registers it,
    /// and returns the request along with a future that will resolve
    /// when the response is received.
    ///
    /// # Arguments
    ///
    /// * `etype` - The event type (method name)
    /// * `args` - Optional positional arguments
    /// * `kwargs` - Optional keyword arguments
    /// * `timeout_duration` - Maximum time to wait for response
    ///
    /// # Returns
    ///
    /// A tuple of (RpcRequest, Future<RpcResponse>)
    pub async fn request(
        &self,
        etype: impl Into<String>,
        args: Option<Vec<Value>>,
        kwargs: Option<HashMap<String, Value>>,
        timeout_duration: Duration,
    ) -> Result<(RpcRequest, impl std::future::Future<Output = Result<RpcResponse>>)> {
        let req = create_rpc_request(etype, args, kwargs);
        let rtype = req.rtype.clone();

        let (tx, rx) = oneshot::channel();

        // Register the pending request
        {
            let mut pending = self.pending.lock().await;
            pending.insert(rtype.clone(), tx);
        }

        // Create a future that will resolve when the response is received
        let pending = self.pending.clone();
        let response_future = async move {
            match timeout(timeout_duration, rx).await {
                Ok(Ok(response)) => Ok(response),
                Ok(Err(_)) => {
                    // Channel closed without response
                    let mut pending = pending.lock().await;
                    pending.remove(&rtype);
                    Err(VmpError::RpcError("Response channel closed".to_string()))
                }
                Err(_) => {
                    // Timeout
                    let mut pending = pending.lock().await;
                    pending.remove(&rtype);
                    Err(VmpError::RpcTimeout(format!(
                        "Request timed out after {:?}",
                        timeout_duration
                    )))
                }
            }
        };

        Ok((req, response_future))
    }

    /// Handle an incoming RPC response
    ///
    /// This should be called when a response is received to correlate
    /// it back to the original request.
    pub async fn handle_response(&self, response: RpcResponse) -> Result<()> {
        let mut pending = self.pending.lock().await;

        if let Some(sender) = pending.remove(&response.etype) {
            sender
                .send(response)
                .map_err(|_| VmpError::RpcError("Failed to send response".to_string()))?;
            Ok(())
        } else {
            Err(VmpError::RpcError(format!(
                "No pending request for response type: {}",
                response.etype
            )))
        }
    }

    /// Cancel a pending request
    pub async fn cancel(&self, rtype: &str) -> bool {
        let mut pending = self.pending.lock().await;
        pending.remove(rtype).is_some()
    }

    /// Get the number of pending requests
    pub async fn pending_count(&self) -> usize {
        let pending = self.pending.lock().await;
        pending.len()
    }

    /// Clear all pending requests
    pub async fn clear(&self) {
        let mut pending = self.pending.lock().await;
        pending.clear();
    }
}

#[cfg(test)]
#[cfg(feature = "tokio")]
mod tests {
    use super::*;
    use serde_json::json;

    #[tokio::test]
    async fn test_generate_request_id() {
        let id1 = generate_request_id();
        let id2 = generate_request_id();

        assert!(id1.starts_with("rpc-"));
        assert_ne!(id1, id2);
    }

    #[tokio::test]
    async fn test_create_rpc_request() {
        let mut kwargs = HashMap::new();
        kwargs.insert("seed".to_string(), json!(100));

        let req = create_rpc_request("render", None, Some(kwargs));

        assert_eq!(req.etype, "render");
        assert!(req.rtype.starts_with("rpc-"));
        assert!(req.kwargs.is_some());
    }

    #[tokio::test]
    async fn test_rpc_manager() {
        let manager = RpcManager::new();

        let (req, response_fut) = manager
            .request("test", None, None, Duration::from_secs(5))
            .await
            .unwrap();

        // Simulate receiving a response
        let response = RpcResponse::success(&req.rtype, json!({"result": "success"}));

        let manager_clone = manager.clone();
        tokio::spawn(async move {
            tokio::time::sleep(Duration::from_millis(100)).await;
            manager_clone.handle_response(response).await.unwrap();
        });

        let response = response_fut.await.unwrap();
        assert_eq!(response.ok, Some(true));
        assert_eq!(response.data, Some(json!({"result": "success"})));
    }

    #[tokio::test]
    async fn test_rpc_timeout() {
        let manager = RpcManager::new();

        let (_req, response_fut) = manager
            .request("test", None, None, Duration::from_millis(100))
            .await
            .unwrap();

        // Don't send a response, let it timeout
        let result = response_fut.await;
        assert!(result.is_err());
        assert!(matches!(result.unwrap_err(), VmpError::RpcTimeout(_)));
    }

    #[tokio::test]
    async fn test_rpc_cancel() {
        let manager = RpcManager::new();

        let (req, _response_fut) = manager
            .request("test", None, None, Duration::from_secs(5))
            .await
            .unwrap();

        assert_eq!(manager.pending_count().await, 1);

        let cancelled = manager.cancel(&req.rtype).await;
        assert!(cancelled);
        assert_eq!(manager.pending_count().await, 0);
    }
}
