import { pack } from 'msgpackr';
import { ZData } from './zdata.js';
import type { VuerComponent, Message } from './types.js';

/**
 * Options for serialization
 */
export interface SerializeOptions {
  /**
   * Whether to recursively serialize nested objects
   * Default: true
   */
  recursive?: boolean;

  /**
   * Whether to use custom ZData encoders from the registry
   * Default: true
   */
  useCustomEncoders?: boolean;

  /**
   * Whether to preserve undefined values (if false, they're removed)
   * Default: false
   */
  preserveUndefined?: boolean;
}

/**
 * Recursively walks through a value and encodes ZData types
 * This handles nested objects, arrays, and VuerComponent trees
 */
function encodeValue(value: unknown, options: Required<SerializeOptions>): unknown {
  // Handle null and undefined
  if (value === null) {
    return null;
  }
  if (value === undefined) {
    return options.preserveUndefined ? undefined : null;
  }

  // Handle primitive types
  if (
    typeof value === 'string' ||
    typeof value === 'number' ||
    typeof value === 'boolean'
  ) {
    return value;
  }

  // Check if it's already ZData
  if (ZData.is_zdata(value)) {
    return value;
  }

  // Try custom encoders if enabled
  if (options.useCustomEncoders) {
    const encoded = ZData.encode(value);
    // If encoding changed the value, return it
    if (encoded !== value) {
      return encoded;
    }
  }

  // Handle arrays recursively
  if (Array.isArray(value)) {
    if (!options.recursive) {
      return value;
    }
    return value.map((item) => encodeValue(item, options));
  }

  // Handle objects recursively
  if (typeof value === 'object') {
    if (!options.recursive) {
      return value;
    }

    const result: Record<string, unknown> = {};
    for (const [key, val] of Object.entries(value)) {
      const encoded = encodeValue(val, options);
      if (encoded !== undefined || options.preserveUndefined) {
        result[key] = encoded;
      }
    }
    return result;
  }

  // Return as-is for other types (functions, symbols, etc.)
  return value;
}

/**
 * Serializes a value to msgpack format
 * Recursively encodes ZData types and handles nested structures
 *
 * @param value - The value to serialize (Message, VuerComponent, or any data)
 * @param options - Serialization options
 * @returns Binary msgpack data as Uint8Array
 *
 * @example
 * ```ts
 * const message: Message = {
 *   ts: Date.now(),
 *   etype: 'UPDATE',
 *   data: { position: [1, 2, 3] }
 * };
 * const binary = serialize(message);
 * ```
 */
export function serialize(
  value: unknown,
  options: SerializeOptions = {}
): Uint8Array {
  const opts: Required<SerializeOptions> = {
    recursive: options.recursive ?? true,
    useCustomEncoders: options.useCustomEncoders ?? true,
    preserveUndefined: options.preserveUndefined ?? false,
  };

  // Recursively encode the value
  const encoded = encodeValue(value, opts);

  // Pack with msgpackr
  return pack(encoded);
}

/**
 * Convenience function to serialize a Message
 */
export function serializeMessage(message: Message, options?: SerializeOptions): Uint8Array {
  return serialize(message, options);
}

/**
 * Convenience function to serialize a VuerComponent
 */
export function serializeComponent(
  component: VuerComponent,
  options?: SerializeOptions
): Uint8Array {
  return serialize(component, options);
}

/**
 * Serialize to base64 string (useful for JSON transport)
 */
export function serializeToBase64(
  value: unknown,
  options?: SerializeOptions
): string {
  const binary = serialize(value, options);
  // Convert Uint8Array to base64
  return Buffer.from(binary).toString('base64');
}
