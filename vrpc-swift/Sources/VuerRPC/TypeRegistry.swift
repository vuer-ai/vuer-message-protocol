//
//  TypeRegistry.swift
//  VuerRPC
//
//  Type registry for custom ZData types
//  Author: Ge Yang
//

import Foundation

/// Type registration information
public struct TypeRegistration: Sendable {
    public let ztype: String
    public let encoder: @Sendable (Any) throws -> ZData
    public let decoder: @Sendable (ZData) throws -> Any
    public let typeChecker: (@Sendable (Any) -> Bool)?

    public init(
        ztype: String,
        encoder: @escaping @Sendable (Any) throws -> ZData,
        decoder: @escaping @Sendable (ZData) throws -> Any,
        typeChecker: (@Sendable (Any) -> Bool)? = nil
    ) {
        self.ztype = ztype
        self.encoder = encoder
        self.decoder = decoder
        self.typeChecker = typeChecker
    }
}

/// Global type registry for custom ZData types
///
/// This allows users to register custom encoders/decoders for types
/// that may not have native Swift equivalents.
public actor TypeRegistry {
    private var types: [String: TypeRegistration] = [:]

    public init() {}

    /// Register a custom type with encoder and decoder functions
    public func register(_ registration: TypeRegistration) {
        types[registration.ztype] = registration
    }

    /// Encode a value using a registered type
    public func encode(ztype: String, value: Any) throws -> ZData {
        guard let registration = types[ztype] else {
            throw VuerRPCError.typeNotRegistered(ztype)
        }
        return try registration.encoder(value)
    }

    /// Decode ZData using a registered type
    public func decode(_ zdata: ZData) throws -> Any {
        guard let registration = types[zdata.ztype] else {
            throw VuerRPCError.typeNotRegistered(zdata.ztype)
        }
        return try registration.decoder(zdata)
    }

    /// Check if a type is registered
    public func isRegistered(ztype: String) -> Bool {
        return types.keys.contains(ztype)
    }

    /// Try to encode a value by checking all registered type checkers
    public func tryEncode(value: Any) -> ZData? {
        for registration in types.values {
            if let checker = registration.typeChecker, checker(value) {
                if let zdata = try? registration.encoder(value) {
                    return zdata
                }
            }
        }
        return nil
    }

    /// Get all registered type names
    public func registeredTypes() -> [String] {
        return Array(types.keys)
    }
}

/// Global shared type registry
public let globalTypeRegistry = TypeRegistry()
