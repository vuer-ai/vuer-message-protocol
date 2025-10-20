//
//  ZData.swift
//  VuerRPC
//
//  ZData encoding system for custom types
//  Author: Ge Yang
//

import Foundation

/// ZData wrapper format for custom data types
public struct ZData: Codable, Equatable, Sendable {
    /// Type identifier (e.g., "numpy.ndarray", "torch.Tensor", "image")
    public var ztype: String

    /// Binary data (for arrays, images, etc.)
    public var b: Data?

    /// Element data type (for arrays/tensors)
    public var dtype: String?

    /// Shape dimensions (for arrays/tensors)
    public var shape: [Int]?

    /// Additional fields for custom types
    public var extra: [String: AnyCodable]

    public init(
        ztype: String,
        b: Data? = nil,
        dtype: String? = nil,
        shape: [Int]? = nil,
        extra: [String: AnyCodable] = [:]
    ) {
        self.ztype = ztype
        self.b = b
        self.dtype = dtype
        self.shape = shape
        self.extra = extra
    }

    /// Add an extra field
    public mutating func setField(key: String, value: AnyCodable) {
        extra[key] = value
    }

    /// Get an extra field
    public func getField(key: String) -> AnyCodable? {
        return extra[key]
    }

    /// Check if this is a specific type
    public func isType(_ ztype: String) -> Bool {
        return self.ztype == ztype
    }

    private enum CodingKeys: String, CodingKey {
        case ztype, b, dtype, shape
    }

    public init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        ztype = try container.decode(String.self, forKey: .ztype)
        b = try container.decodeIfPresent(Data.self, forKey: .b)
        dtype = try container.decodeIfPresent(String.self, forKey: .dtype)
        shape = try container.decodeIfPresent([Int].self, forKey: .shape)

        // Decode additional properties
        let additionalContainer = try decoder.container(keyedBy: DynamicCodingKeys.self)
        var extraFields: [String: AnyCodable] = [:]
        for key in additionalContainer.allKeys where !["ztype", "b", "dtype", "shape"].contains(key.stringValue) {
            if let value = try? additionalContainer.decode(AnyCodable.self, forKey: key) {
                extraFields[key.stringValue] = value
            }
        }
        extra = extraFields
    }

    public func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(ztype, forKey: .ztype)
        try container.encodeIfPresent(b, forKey: .b)
        try container.encodeIfPresent(dtype, forKey: .dtype)
        try container.encodeIfPresent(shape, forKey: .shape)

        // Encode additional properties
        var additionalContainer = encoder.container(keyedBy: DynamicCodingKeys.self)
        for (key, value) in extra {
            let codingKey = DynamicCodingKeys(stringValue: key)!
            try additionalContainer.encode(value, forKey: codingKey)
        }
    }
}

/// Protocol for types that can be converted to/from ZData
public protocol ZDataConvertible {
    /// The type identifier for this type
    static var ztype: String { get }

    /// Encode this value to ZData format
    func toZData() throws -> ZData

    /// Decode from ZData format
    static func fromZData(_ zdata: ZData) throws -> Self

    /// Check if this type is available in the current environment
    static var isAvailable: Bool { get }
}

/// Default implementation
extension ZDataConvertible {
    public static var isAvailable: Bool { true }
}

/// Fallback type for when a ZData type is not available
public struct UnknownType: Codable, Equatable, Sendable {
    public let zdata: ZData

    public init(zdata: ZData) {
        self.zdata = zdata
    }

    public var ztype: String {
        return zdata.ztype
    }
}

// MARK: - Helper Types

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
