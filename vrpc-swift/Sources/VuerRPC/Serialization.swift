//
//  Serialization.swift
//  VuerRPC
//
//  MessagePack serialization for VMP
//  Author: Ge Yang
//

import Foundation
import MessagePack

/// Serialization options
public struct SerializationOptions: Sendable {
    /// Recursively encode nested structures
    public var recursive: Bool

    /// Use the global type registry for custom types
    public var useTypeRegistry: Bool

    public init(recursive: Bool = true, useTypeRegistry: Bool = true) {
        self.recursive = recursive
        self.useTypeRegistry = useTypeRegistry
    }

    public static let `default` = SerializationOptions()
}

/// Serialize a Codable value to MessagePack binary format
public func serialize<T: Codable>(_ value: T, options: SerializationOptions = .default) throws -> Data {
    do {
        let encoder = MessagePackEncoder()
        return try encoder.encode(value)
    } catch {
        throw VuerRPCError.serializationError(error.localizedDescription)
    }
}

/// Deserialize from MessagePack binary format
public func deserialize<T: Codable>(_ data: Data, options: SerializationOptions = .default) throws -> T {
    do {
        let decoder = MessagePackDecoder()
        return try decoder.decode(T.self, from: data)
    } catch {
        throw VuerRPCError.deserializationError(error.localizedDescription)
    }
}

/// Serialize a message to MessagePack
public func serializeMessage(_ message: Message) throws -> Data {
    return try serialize(message)
}

/// Deserialize a message from MessagePack
public func deserializeMessage(_ data: Data) throws -> Message {
    return try deserialize(data)
}

/// Serialize a Vuer component tree to MessagePack
public func serializeComponent(_ component: VuerComponent) throws -> Data {
    return try serialize(component)
}

/// Deserialize a Vuer component from MessagePack
public func deserializeComponent(_ data: Data) throws -> VuerComponent {
    return try deserialize(data)
}

/// Serialize to base64-encoded MessagePack
public func serializeToBase64<T: Codable>(_ value: T) throws -> String {
    let data = try serialize(value)
    return data.base64EncodedString()
}

/// Deserialize from base64-encoded MessagePack
public func deserializeFromBase64<T: Codable>(_ encoded: String) throws -> T {
    guard let data = Data(base64Encoded: encoded) else {
        throw VuerRPCError.deserializationError("Invalid base64 string")
    }
    return try deserialize(data)
}

/// Helper to convert ZData to MessagePack bytes
public func zdataToBytes(_ zdata: ZData) throws -> Data {
    return try serialize(zdata)
}

/// Helper to convert MessagePack bytes to ZData
public func bytesToZData(_ data: Data) throws -> ZData {
    return try deserialize(data)
}

/// Validate message structure
public func validateMessage(_ message: Message) throws {
    if message.etype.isEmpty {
        throw VuerRPCError.invalidMessage("Message etype cannot be empty")
    }

    // RPC requests must have rtype
    if (message.args != nil || message.kwargs != nil) && message.rtype == nil {
        throw VuerRPCError.invalidMessage("RPC request must have rtype field")
    }
}
