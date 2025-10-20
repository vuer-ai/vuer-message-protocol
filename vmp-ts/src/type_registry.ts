/**
 * Type registry for ZData encoding/decoding.
 *
 * Provides a global registry that can be extended by users to add custom types.
 * This module matches the Python vmp-py TypeRegistry architecture.
 */

import type { ZDataDict, TypeEncoder, TypeDecoder, TypeChecker } from './types.js';

/**
 * Registry entry for type checkers
 */
interface TypeCheckerEntry {
  checker: TypeChecker;
  typeName: string;
  encoder: TypeEncoder;
}

/**
 * Registry for custom type encoders and decoders.
 *
 * This registry can be extended by users to add support for custom types.
 * The registry supports three ways of registering types:
 * 1. By exact type class/constructor
 * 2. By custom type checker function
 * 3. Both (recommended for reliability)
 */
export class TypeRegistry {
  private encoders = new Map<Function, { typeName: string; encoder: TypeEncoder }>();
  private decoders = new Map<string, TypeDecoder>();
  private typeCheckers: TypeCheckerEntry[] = [];

  /**
   * Register a type for encoding/decoding.
   *
   * @param typeName - Unique identifier for this type (e.g., "numpy.ndarray")
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
   * function encodePoint(p: Point): ZDataDict {
   *   return {
   *     ztype: "custom.Point",
   *     b: new TextEncoder().encode(`${p.x},${p.y}`)
   *   };
   * }
   *
   * function decodePoint(z: ZDataDict): Point {
   *   const [x, y] = new TextDecoder().decode(z.b).split(",").map(Number);
   *   return new Point(x, y);
   * }
   *
   * TYPE_REGISTRY.register(
   *   "custom.Point",
   *   encodePoint,
   *   decodePoint,
   *   Point  // type class
   * );
   * ```
   */
  register(
    typeName: string,
    encoder: TypeEncoder,
    decoder: TypeDecoder,
    typeClass?: Function,
    typeChecker?: TypeChecker
  ): void {
    // Register decoder
    this.decoders.set(typeName, decoder);

    // Register encoder by type class
    if (typeClass !== undefined) {
      this.encoders.set(typeClass, { typeName, encoder });
    }

    // Register encoder by type checker
    if (typeChecker !== undefined) {
      this.typeCheckers.push({ checker: typeChecker, typeName, encoder });
    }
  }

  /**
   * Encode data using registered encoders.
   *
   * Returns the encoded ZDataDict if a matching encoder is found,
   * otherwise returns the data unchanged.
   *
   * @param data - Data to encode
   * @returns ZDataDict or original data
   */
  encode(data: unknown): unknown {
    // Check by exact type/constructor
    if (data !== null && typeof data === 'object') {
      const constructor = (data as object).constructor;
      if (constructor && this.encoders.has(constructor)) {
        const entry = this.encoders.get(constructor)!;
        return entry.encoder(data);
      }
    }

    // Check using custom type checkers
    for (const { checker, encoder } of this.typeCheckers) {
      if (checker(data)) {
        return encoder(data);
      }
    }

    // No encoder found, return as-is
    return data;
  }

  /**
   * Decode ZData using registered decoders.
   *
   * Returns the decoded object if zdata is a valid ZData dict,
   * otherwise returns the data unchanged.
   *
   * @param zdata - ZData dictionary or plain data
   * @returns Decoded object or original data
   * @throws TypeError if zdata has an unknown ztype
   */
  decode(zdata: unknown): unknown {
    if (!this.isZData(zdata)) {
      return zdata;
    }

    const zdataDict = zdata as ZDataDict;
    const ztype = zdataDict.ztype;

    if (!this.decoders.has(ztype)) {
      throw new TypeError(`Unknown ZData type: ${ztype}`);
    }

    const decoder = this.decoders.get(ztype)!;
    return decoder(zdataDict);
  }

  /**
   * Check if data is a ZData encoded object.
   *
   * @param data - Data to check
   * @returns True if data is a ZData dictionary
   */
  isZData(data: unknown): data is ZDataDict {
    return (
      typeof data === 'object' &&
      data !== null &&
      'ztype' in data &&
      typeof (data as ZDataDict).ztype === 'string'
    );
  }

  /**
   * Get the ztype of a ZData object.
   *
   * @param data - Data to check
   * @returns The ztype string if data is ZData, undefined otherwise
   */
  getZType(data: unknown): string | undefined {
    if (this.isZData(data)) {
      return (data as ZDataDict).ztype;
    }
    return undefined;
  }

  /**
   * List all registered type names.
   *
   * @returns Array of registered ztype names
   */
  listRegisteredTypes(): string[] {
    return Array.from(this.decoders.keys());
  }
}

/**
 * Global type registry - users can extend this
 */
export const TYPE_REGISTRY = new TypeRegistry();
