//! Error types for VMP
//!
//! Author: Ge Yang

use thiserror::Error;

#[derive(Error, Debug)]
pub enum VmpError {
    #[error("Serialization error: {0}")]
    Serialization(String),

    #[error("Deserialization error: {0}")]
    Deserialization(String),

    #[error("Type conversion error: {0}")]
    TypeConversion(String),

    #[error("Type not registered: {0}")]
    TypeNotRegistered(String),

    #[error("RPC timeout: {0}")]
    RpcTimeout(String),

    #[error("RPC error: {0}")]
    RpcError(String),

    #[error("Invalid message format: {0}")]
    InvalidMessage(String),

    #[error("Missing required field: {0}")]
    MissingField(String),

    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),

    #[error("MessagePack encode error: {0}")]
    MsgPackEncode(#[from] rmp_serde::encode::Error),

    #[error("MessagePack decode error: {0}")]
    MsgPackDecode(#[from] rmp_serde::decode::Error),

    #[error("JSON error: {0}")]
    Json(#[from] serde_json::Error),

    #[cfg(feature = "image")]
    #[error("Image error: {0}")]
    Image(#[from] image::ImageError),
}

pub type Result<T> = std::result::Result<T, VmpError>;
