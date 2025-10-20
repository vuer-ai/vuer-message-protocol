//
//  Errors.swift
//  VuerRPC
//
//  Error types for VuerRPC
//  Author: Ge Yang
//

import Foundation

/// Errors that can occur in VuerRPC
public enum VuerRPCError: Error, LocalizedError, Sendable {
    case serializationError(String)
    case deserializationError(String)
    case typeConversionError(String)
    case typeNotRegistered(String)
    case rpcTimeout(String)
    case rpcError(String)
    case invalidMessage(String)
    case missingField(String)

    public var errorDescription: String? {
        switch self {
        case .serializationError(let message):
            return "Serialization error: \(message)"
        case .deserializationError(let message):
            return "Deserialization error: \(message)"
        case .typeConversionError(let message):
            return "Type conversion error: \(message)"
        case .typeNotRegistered(let message):
            return "Type not registered: \(message)"
        case .rpcTimeout(let message):
            return "RPC timeout: \(message)"
        case .rpcError(let message):
            return "RPC error: \(message)"
        case .invalidMessage(let message):
            return "Invalid message format: \(message)"
        case .missingField(let message):
            return "Missing required field: \(message)"
        }
    }
}

/// Type conversion fallback for unavailable types
public struct TypeConversionFallback {
    /// Get a helpful error message for a missing type
    public static func missingTypeError(ztype: String) -> VuerRPCError {
        switch ztype {
        case "numpy.ndarray":
            return .typeConversionError(
                "NumPy array support requires additional implementation. " +
                "The type '\(ztype)' is not available in this environment."
            )
        case "image":
            return .typeConversionError(
                "Image support requires additional implementation. " +
                "The type '\(ztype)' is not available in this environment."
            )
        default:
            return .typeNotRegistered(
                "Type '\(ztype)' is not available. " +
                "It may require additional dependencies or implementation."
            )
        }
    }
}
