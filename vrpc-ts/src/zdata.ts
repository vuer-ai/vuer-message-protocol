/**
 * ZData - Extensible type encoding system for binary serialization.
 *
 * Provides encoding/decoding for TypedArrays and allows registration of custom types.
 *
 * Basic usage:
 * ```typescript
 * import { ZData } from '@vuer-ai/vmp-ts';
 *
 * const data = new Float32Array([1, 2, 3]);
 * const encoded = ZData.encode(data);
 * const decoded = ZData.decode(encoded);
 * ```
 *
 * Custom types:
 * ```typescript
 * class Point {
 *   constructor(public x: number, public y: number) {}
 * }
 *
 * ZData.register_type(
 *   "custom.Point",
 *   (p) => ({ ztype: "custom.Point", b: new TextEncoder().encode(`${p.x},${p.y}`) }),
 *   (z) => {
 *     const [x, y] = new TextDecoder().decode(z.b).split(",").map(Number);
 *     return new Point(x, y);
 *   },
 *   Point
 * );
 * ```
 */

import type { ZDataDict, TypeEncoder, TypeDecoder, TypeChecker } from './types.js';
import { TYPE_REGISTRY } from './type_registry.js';

// Import built-in types (TypedArrays are always available)
import './builtin_types.js';

/**
 * Main interface for ZData encoding/decoding.
 *
 * Uses the global TYPE_REGISTRY which can be extended by:
 * 1. Registering custom types with ZData.register_type()
 * 2. Directly accessing TYPE_REGISTRY in external libraries
 */
export class ZData {
  /**
   * Encode data to ZData format if a matching encoder is registered.
   *
   * @param data - Data to encode (TypedArray, custom objects, etc.)
   * @returns ZDataDict if data type is registered, otherwise returns data unchanged
   *
   * @example
   * ```typescript
   * const arr = new Float32Array([1, 2, 3]);
   * const encoded = ZData.encode(arr);
   * console.log(encoded.ztype); // "Float32Array"
   * ```
   */
  static encode(data: unknown): unknown {
    return TYPE_REGISTRY.encode(data);
  }

  /**
   * Decode ZData back to original type.
   *
   * @param zdata - ZData dictionary or plain data
   * @returns Decoded object if zdata is valid ZData, otherwise returns zdata unchanged
   * @throws TypeError if zdata has an unknown ztype
   *
   * @example
   * ```typescript
   * const encoded = ZData.encode(new Float32Array([1, 2, 3]));
   * const decoded = ZData.decode(encoded);
   * console.log(decoded); // Float32Array [1, 2, 3]
   * ```
   */
  static decode(zdata: unknown): unknown {
    return TYPE_REGISTRY.decode(zdata);
  }

  /**
   * Check if data is a ZData encoded object.
   *
   * @param data - Data to check
   * @returns True if data is a ZData dictionary
   *
   * @example
   * ```typescript
   * const arr = new Float32Array([1, 2, 3]);
   * const encoded = ZData.encode(arr);
   * console.log(ZData.is_zdata(encoded)); // true
   * console.log(ZData.is_zdata(arr)); // false
   * ```
   */
  static is_zdata(data: unknown): data is ZDataDict {
    return TYPE_REGISTRY.isZData(data);
  }

  /**
   * Get the ztype of a ZData object.
   *
   * @param data - Data to check
   * @returns The ztype string if data is ZData, undefined otherwise
   *
   * @example
   * ```typescript
   * const encoded = ZData.encode(new Float32Array([1, 2, 3]));
   * console.log(ZData.get_ztype(encoded)); // "Float32Array"
   * ```
   */
  static get_ztype(data: unknown): string | undefined {
    return TYPE_REGISTRY.getZType(data);
  }

  /**
   * Register a custom type for encoding/decoding.
   *
   * @param typeName - Unique identifier for this type (e.g., "custom.MyType")
   * @param encoder - Function that encodes data to ZDataDict
   * @param decoder - Function that decodes ZDataDict back to original type
   * @param typeClass - Optional type class/constructor for direct type checking
   * @param typeChecker - Optional function for custom type checking
   *
   * @example
   * ```typescript
   * class Point {
   *   constructor(public x: number, public y: number) {}
   * }
   *
   * ZData.register_type(
   *   "custom.Point",
   *   (p: Point) => ({
   *     ztype: "custom.Point",
   *     b: new TextEncoder().encode(`${p.x},${p.y}`)
   *   }),
   *   (z: ZDataDict) => {
   *     const [x, y] = new TextDecoder().decode(z.b as Uint8Array)
   *       .split(",").map(Number);
   *     return new Point(x, y);
   *   },
   *   Point
   * );
   *
   * const point = new Point(1.0, 2.0);
   * const encoded = ZData.encode(point);
   * const decoded = ZData.decode(encoded);
   * ```
   */
  static register_type(
    typeName: string,
    encoder: TypeEncoder,
    decoder: TypeDecoder,
    typeClass?: Function,
    typeChecker?: TypeChecker
  ): void {
    TYPE_REGISTRY.register(typeName, encoder, decoder, typeClass, typeChecker);
  }

  /**
   * List all registered type names.
   *
   * @returns List of registered ztype names
   *
   * @example
   * ```typescript
   * const types = ZData.list_types();
   * console.log(types); // ['Float32Array', 'Float64Array', ...]
   * ```
   */
  static list_types(): string[] {
    return TYPE_REGISTRY.listRegisteredTypes();
  }

  /**
   * Identity function that wraps data with a ztype tag without encoding.
   *
   * Useful for adding type information to data without performing binary encoding.
   * The data is kept as-is, only wrapped in a ZDataDict with the specified ztype.
   *
   * @param ztype - Type identifier to tag the data with
   * @param data - Data to wrap (kept as-is)
   * @returns ZDataDict with ztype and original data
   *
   * @example
   * ```typescript
   * // Tag data without encoding
   * const tagged = ZData.identity('custom.MyType', { x: 1, y: 2 });
   * // Returns: { ztype: 'custom.MyType', data: { x: 1, y: 2 } }
   *
   * // Useful for polymorphic data structures
   * const geometries = [
   *   ZData.identity('sphere', { radius: 1 }),
   *   ZData.identity('box', { size: [1, 2, 3] }),
   *   ZData.identity('cylinder', { radius: 0.5, height: 2 }),
   * ];
   * ```
   */
  static identity(ztype: string, data: unknown): ZDataDict {
    return {
      ztype,
      data,
    };
  }
}

/**
 * Export the TYPE_REGISTRY for advanced use cases
 */
export { TYPE_REGISTRY } from './type_registry.js';
