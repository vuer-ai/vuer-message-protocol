import { unpack } from 'msgpackr';
import { ZData } from './zdata.js';
import type { Message, VuerComponent, ZDataDict } from './types.js';

/**
 * Options for deserialization
 */
export interface DeserializeOptions {
  /**
   * Whether to recursively deserialize nested objects
   * Default: true
   */
  recursive?: boolean;

  /**
   * Whether to decode ZData types using registry decoders
   * Default: true
   */
  decodeZData?: boolean;

  /**
   * Whether to preserve ZData objects as-is instead of decoding them
   * Useful if you want to handle ZData manually
   * Default: false
   */
  preserveZData?: boolean;
}

/**
 * Recursively walks through a value and decodes ZData types
 */
function decodeValue(value: unknown, options: Required<DeserializeOptions>): unknown {
  // Handle null and undefined
  if (value === null || value === undefined) {
    return value;
  }

  // Handle primitive types
  if (
    typeof value === 'string' ||
    typeof value === 'number' ||
    typeof value === 'boolean'
  ) {
    return value;
  }

  // Handle ZData objects
  if (ZData.is_zdata(value)) {
    if (options.preserveZData) {
      return value;
    }
    if (options.decodeZData) {
      try {
        const decoded = ZData.decode(value);
        return decoded;
      } catch (error) {
        // If unknown type, return as-is or rethrow based on option
        if (error instanceof TypeError && error.message.startsWith('Unknown ZData type')) {
          // Return as-is for unknown types if preserveZData fallback
          return value;
        }
        throw error;
      }
    }
    // If decoding disabled, return as-is
    return value;
  }

  // Handle arrays recursively
  if (Array.isArray(value)) {
    if (!options.recursive) {
      return value;
    }
    return value.map((item) => decodeValue(item, options));
  }

  // Handle objects recursively
  if (typeof value === 'object') {
    if (!options.recursive) {
      return value;
    }

    const result: Record<string, unknown> = {};
    for (const [key, val] of Object.entries(value)) {
      result[key] = decodeValue(val, options);
    }
    return result;
  }

  // Return as-is for other types
  return value;
}

/**
 * Deserializes msgpack binary data back to JavaScript values
 * Recursively decodes ZData types using registered decoders
 *
 * @param data - Binary msgpack data (Uint8Array or Buffer)
 * @param options - Deserialization options
 * @returns Deserialized value
 *
 * @example
 * ```ts
 * const binary = await fetch('/api/message').then(r => r.arrayBuffer());
 * const message = deserialize(new Uint8Array(binary)) as Message;
 * console.log(message.etype, message.data);
 * ```
 */
export function deserialize<T = unknown>(
  data: Uint8Array | Buffer,
  options: DeserializeOptions = {}
): T {
  const opts: Required<DeserializeOptions> = {
    recursive: options.recursive ?? true,
    decodeZData: options.decodeZData ?? true,
    preserveZData: options.preserveZData ?? false,
  };

  // Unpack with msgpackr
  const unpacked = unpack(data);

  // Recursively decode the value
  return decodeValue(unpacked, opts) as T;
}

/**
 * Convenience function to deserialize a Message
 */
export function deserializeMessage(
  data: Uint8Array | Buffer,
  options?: DeserializeOptions
): Message {
  return deserialize<Message>(data, options);
}

/**
 * Convenience function to deserialize a VuerComponent
 */
export function deserializeComponent(
  data: Uint8Array | Buffer,
  options?: DeserializeOptions
): VuerComponent {
  return deserialize<VuerComponent>(data, options);
}

/**
 * Deserialize from base64 string
 */
export function deserializeFromBase64<T = unknown>(
  base64: string,
  options?: DeserializeOptions
): T {
  const binary = Buffer.from(base64, 'base64');
  return deserialize<T>(binary, options);
}

/**
 * Type-safe deserializer that validates the structure
 * This is useful when you want to ensure the deserialized data matches expected schema
 */
export function deserializeWithValidation<T>(
  data: Uint8Array | Buffer,
  validator: (value: unknown) => value is T,
  options?: DeserializeOptions
): T {
  const result = deserialize(data, options);
  if (!validator(result)) {
    throw new Error('Deserialized data does not match expected schema');
  }
  return result;
}

/**
 * Type guard for Message
 */
export function isMessage(value: unknown): value is Message {
  return (
    typeof value === 'object' &&
    value !== null &&
    'ts' in value &&
    'etype' in value &&
    typeof (value as Message).ts === 'number' &&
    typeof (value as Message).etype === 'string'
  );
}

/**
 * Type guard for VuerComponent
 */
export function isVuerComponent(value: unknown): value is VuerComponent {
  return (
    typeof value === 'object' &&
    value !== null &&
    'tag' in value &&
    typeof (value as VuerComponent).tag === 'string'
  );
}

/**
 * Type guard for ZDataDict
 * Re-export from ZData for convenience
 */
export function isZData(value: unknown): value is ZDataDict {
  return ZData.is_zdata(value);
}
