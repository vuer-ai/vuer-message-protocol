//
//  AnyCodable.swift
//  VuerRPC
//
//  Type-erased Codable wrapper for handling dynamic values
//  Author: Ge Yang
//

import Foundation

/// A type-erased Codable value
public struct AnyCodable: Codable, Equatable, Sendable {
    public let value: Any

    public init(_ value: Any) {
        self.value = value
    }

    public init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()

        if container.decodeNil() {
            self.value = NSNull()
        } else if let bool = try? container.decode(Bool.self) {
            self.value = bool
        } else if let int = try? container.decode(Int.self) {
            self.value = int
        } else if let double = try? container.decode(Double.self) {
            self.value = double
        } else if let string = try? container.decode(String.self) {
            self.value = string
        } else if let array = try? container.decode([AnyCodable].self) {
            self.value = array.map { $0.value }
        } else if let dictionary = try? container.decode([String: AnyCodable].self) {
            self.value = dictionary.mapValues { $0.value }
        } else {
            throw DecodingError.dataCorruptedError(
                in: container,
                debugDescription: "AnyCodable value cannot be decoded"
            )
        }
    }

    public func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()

        switch value {
        case is NSNull:
            try container.encodeNil()
        case let bool as Bool:
            try container.encode(bool)
        case let int as Int:
            try container.encode(int)
        case let int8 as Int8:
            try container.encode(int8)
        case let int16 as Int16:
            try container.encode(int16)
        case let int32 as Int32:
            try container.encode(int32)
        case let int64 as Int64:
            try container.encode(int64)
        case let uint as UInt:
            try container.encode(uint)
        case let uint8 as UInt8:
            try container.encode(uint8)
        case let uint16 as UInt16:
            try container.encode(uint16)
        case let uint32 as UInt32:
            try container.encode(uint32)
        case let uint64 as UInt64:
            try container.encode(uint64)
        case let float as Float:
            try container.encode(float)
        case let double as Double:
            try container.encode(double)
        case let string as String:
            try container.encode(string)
        case let array as [Any]:
            try container.encode(array.map { AnyCodable($0) })
        case let dictionary as [String: Any]:
            try container.encode(dictionary.mapValues { AnyCodable($0) })
        default:
            let context = EncodingError.Context(
                codingPath: container.codingPath,
                debugDescription: "AnyCodable value cannot be encoded"
            )
            throw EncodingError.invalidValue(value, context)
        }
    }

    public static func == (lhs: AnyCodable, rhs: AnyCodable) -> Bool {
        switch (lhs.value, rhs.value) {
        case is (NSNull, NSNull):
            return true
        case let (lhs as Bool, rhs as Bool):
            return lhs == rhs
        case let (lhs as Int, rhs as Int):
            return lhs == rhs
        case let (lhs as Double, rhs as Double):
            return lhs == rhs
        case let (lhs as String, rhs as String):
            return lhs == rhs
        case let (lhs as [Any], rhs as [Any]):
            return lhs.map { AnyCodable($0) } == rhs.map { AnyCodable($0) }
        case let (lhs as [String: Any], rhs as [String: Any]):
            return lhs.mapValues { AnyCodable($0) } == rhs.mapValues { AnyCodable($0) }
        default:
            return false
        }
    }
}

// MARK: - Convenience Extensions

extension AnyCodable: ExpressibleByNilLiteral {
    public init(nilLiteral: ()) {
        self.value = NSNull()
    }
}

extension AnyCodable: ExpressibleByBooleanLiteral {
    public init(booleanLiteral value: Bool) {
        self.value = value
    }
}

extension AnyCodable: ExpressibleByIntegerLiteral {
    public init(integerLiteral value: Int) {
        self.value = value
    }
}

extension AnyCodable: ExpressibleByFloatLiteral {
    public init(floatLiteral value: Double) {
        self.value = value
    }
}

extension AnyCodable: ExpressibleByStringLiteral {
    public init(stringLiteral value: String) {
        self.value = value
    }
}

extension AnyCodable: ExpressibleByArrayLiteral {
    public init(arrayLiteral elements: Any...) {
        self.value = elements
    }
}

extension AnyCodable: ExpressibleByDictionaryLiteral {
    public init(dictionaryLiteral elements: (String, Any)...) {
        self.value = Dictionary(uniqueKeysWithValues: elements)
    }
}
