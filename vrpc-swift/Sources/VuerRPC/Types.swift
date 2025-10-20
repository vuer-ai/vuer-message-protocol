//
//  Types.swift
//  VuerRPC
//
//  Core type definitions for the Vuer Message Protocol
//  Author: Ge Yang
//

import Foundation

/// Timestamp in milliseconds since Unix epoch
public typealias Timestamp = Int64

/// Generic message envelope with all possible fields
public struct Message: Codable, Equatable, Sendable {
    /// Timestamp in milliseconds
    public var ts: Timestamp

    /// Event type or queue name
    public var etype: String

    /// Response type (RPC only)
    public var rtype: String?

    /// Positional arguments (RPC)
    public var args: [AnyCodable]?

    /// Keyword arguments (RPC)
    public var kwargs: [String: AnyCodable]?

    /// Server payload
    public var data: AnyCodable?

    /// Client payload
    public var value: AnyCodable?

    public init(
        ts: Timestamp? = nil,
        etype: String,
        rtype: String? = nil,
        args: [AnyCodable]? = nil,
        kwargs: [String: AnyCodable]? = nil,
        data: AnyCodable? = nil,
        value: AnyCodable? = nil
    ) {
        self.ts = ts ?? Timestamp(Date().timeIntervalSince1970 * 1000)
        self.etype = etype
        self.rtype = rtype
        self.args = args
        self.kwargs = kwargs
        self.data = data
        self.value = value
    }
}

/// Client-to-server event (uses value for payload)
public struct ClientEvent: Codable, Equatable, Sendable {
    /// Timestamp in milliseconds
    public var ts: Timestamp

    /// Event type
    public var etype: String

    /// Response type (for RPC requests)
    public var rtype: String?

    /// Client payload
    public var value: AnyCodable

    public init(
        ts: Timestamp? = nil,
        etype: String,
        rtype: String? = nil,
        value: AnyCodable
    ) {
        self.ts = ts ?? Timestamp(Date().timeIntervalSince1970 * 1000)
        self.etype = etype
        self.rtype = rtype
        self.value = value
    }
}

/// Server-to-client event (uses data for payload)
public struct ServerEvent: Codable, Equatable, Sendable {
    /// Timestamp in milliseconds
    public var ts: Timestamp

    /// Event type
    public var etype: String

    /// Server payload
    public var data: AnyCodable

    public init(
        ts: Timestamp? = nil,
        etype: String,
        data: AnyCodable
    ) {
        self.ts = ts ?? Timestamp(Date().timeIntervalSince1970 * 1000)
        self.etype = etype
        self.data = data
    }
}

/// RPC Request (includes rtype for response routing)
public struct RPCRequest: Codable, Equatable, Sendable {
    /// Timestamp in milliseconds
    public var ts: Timestamp

    /// Event type (method name)
    public var etype: String

    /// Response type (required for RPC)
    public var rtype: String

    /// Positional arguments
    public var args: [AnyCodable]?

    /// Keyword arguments
    public var kwargs: [String: AnyCodable]?

    public init(
        ts: Timestamp? = nil,
        etype: String,
        rtype: String,
        args: [AnyCodable]? = nil,
        kwargs: [String: AnyCodable]? = nil
    ) {
        self.ts = ts ?? Timestamp(Date().timeIntervalSince1970 * 1000)
        self.etype = etype
        self.rtype = rtype
        self.args = args
        self.kwargs = kwargs
    }
}

/// RPC Response
public struct RPCResponse: Codable, Equatable, Sendable {
    /// Timestamp in milliseconds
    public var ts: Timestamp

    /// Event type (matches request's rtype)
    public var etype: String

    /// Response payload (server)
    public var data: AnyCodable?

    /// Response payload (client)
    public var value: AnyCodable?

    /// Success flag
    public var ok: Bool?

    /// Error message
    public var error: String?

    public init(
        ts: Timestamp? = nil,
        etype: String,
        data: AnyCodable? = nil,
        value: AnyCodable? = nil,
        ok: Bool? = nil,
        error: String? = nil
    ) {
        self.ts = ts ?? Timestamp(Date().timeIntervalSince1970 * 1000)
        self.etype = etype
        self.data = data
        self.value = value
        self.ok = ok
        self.error = error
    }

    /// Create a successful RPC response
    public static func success(etype: String, data: AnyCodable) -> RPCResponse {
        RPCResponse(etype: etype, data: data, ok: true)
    }

    /// Create a failed RPC response
    public static func failure(etype: String, error: String) -> RPCResponse {
        RPCResponse(etype: etype, ok: false, error: error)
    }
}

/// Vuer component schema (nested structure)
public struct VuerComponent: Codable, Equatable, Sendable {
    /// Component type
    public var tag: String

    /// Nested components
    public var children: [VuerComponent]?

    /// Additional properties
    public var properties: [String: AnyCodable]

    public init(
        tag: String,
        children: [VuerComponent]? = nil,
        properties: [String: AnyCodable] = [:]
    ) {
        self.tag = tag
        self.children = children
        self.properties = properties
    }

    /// Add a child component
    public mutating func addChild(_ child: VuerComponent) {
        if children == nil {
            children = []
        }
        children?.append(child)
    }

    /// Set a property
    public mutating func setProperty(key: String, value: AnyCodable) {
        properties[key] = value
    }

    private enum CodingKeys: String, CodingKey {
        case tag, children
    }

    public init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        tag = try container.decode(String.self, forKey: .tag)
        children = try container.decodeIfPresent([VuerComponent].self, forKey: .children)

        // Decode additional properties
        let additionalContainer = try decoder.container(keyedBy: DynamicCodingKeys.self)
        var props: [String: AnyCodable] = [:]
        for key in additionalContainer.allKeys where key.stringValue != "tag" && key.stringValue != "children" {
            if let value = try? additionalContainer.decode(AnyCodable.self, forKey: key) {
                props[key.stringValue] = value
            }
        }
        properties = props
    }

    public func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(tag, forKey: .tag)
        try container.encodeIfPresent(children, forKey: .children)

        // Encode additional properties
        var additionalContainer = encoder.container(keyedBy: DynamicCodingKeys.self)
        for (key, value) in properties {
            let codingKey = DynamicCodingKeys(stringValue: key)!
            try additionalContainer.encode(value, forKey: codingKey)
        }
    }
}

// MARK: - Helper Types

/// Dynamic coding keys for flexible dictionary encoding/decoding
private struct DynamicCodingKeys: CodingKey {
    var stringValue: String
    var intValue: Int?

    init?(stringValue: String) {
        self.stringValue = stringValue
        self.intValue = nil
    }

    init?(intValue: Int) {
        self.stringValue = "\(intValue)"
        self.intValue = intValue
    }
}
