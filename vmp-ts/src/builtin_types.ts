/**
 * Built-in type encoders/decoders for ZData.
 *
 * This module registers TypedArray support by default.
 * Automatically imported when you import ZData.
 */

import { TYPE_REGISTRY } from './type_registry.js';
import type { ZDataDict } from './types.js';

// ============================================================================
// TypedArray Support
// ============================================================================

/**
 * Register TypedArray types
 * These are the JavaScript equivalents of NumPy arrays
 */

// Float32Array - Most common for 3D graphics (equivalent to np.float32)
TYPE_REGISTRY.register(
  'Float32Array',
  (data: unknown): ZDataDict | null => {
    if (!(data instanceof Float32Array)) return null;
    return {
      ztype: 'Float32Array',
      b: new Uint8Array(data.buffer, data.byteOffset, data.byteLength),
      length: data.length,
    };
  },
  (zdata: ZDataDict): Float32Array => {
    // msgpackr deserializes as Buffer in Node.js, Uint8Array in browser
    const bytes = Buffer.from(zdata.b as Uint8Array);
    return new Float32Array(bytes.buffer, bytes.byteOffset, zdata.length as number);
  },
  Float32Array
);

// Float64Array - Double precision (equivalent to np.float64)
TYPE_REGISTRY.register(
  'Float64Array',
  (data: unknown): ZDataDict | null => {
    if (!(data instanceof Float64Array)) return null;
    return {
      ztype: 'Float64Array',
      b: new Uint8Array(data.buffer, data.byteOffset, data.byteLength),
      length: data.length,
    };
  },
  (zdata: ZDataDict): Float64Array => {
    const bytes = Buffer.from(zdata.b as Uint8Array);
    return new Float64Array(bytes.buffer, bytes.byteOffset, zdata.length as number);
  },
  Float64Array
);

// Uint8Array - For colors, images (equivalent to np.uint8)
TYPE_REGISTRY.register(
  'Uint8Array',
  (data: unknown): ZDataDict | null => {
    if (!(data instanceof Uint8Array)) return null;
    return {
      ztype: 'Uint8Array',
      b: data,
      length: data.length,
    };
  },
  (zdata: ZDataDict): Uint8Array => {
    return Buffer.from(zdata.b as Uint8Array);
  },
  Uint8Array
);

// Uint16Array - For compressed data, indices (equivalent to np.uint16)
TYPE_REGISTRY.register(
  'Uint16Array',
  (data: unknown): ZDataDict | null => {
    if (!(data instanceof Uint16Array)) return null;
    return {
      ztype: 'Uint16Array',
      b: new Uint8Array(data.buffer, data.byteOffset, data.byteLength),
      length: data.length,
    };
  },
  (zdata: ZDataDict): Uint16Array => {
    const bytes = Buffer.from(zdata.b as Uint8Array);
    return new Uint16Array(bytes.buffer, bytes.byteOffset, zdata.length as number);
  },
  Uint16Array
);

// Uint32Array - For large mesh indices (equivalent to np.uint32)
TYPE_REGISTRY.register(
  'Uint32Array',
  (data: unknown): ZDataDict | null => {
    if (!(data instanceof Uint32Array)) return null;
    return {
      ztype: 'Uint32Array',
      b: new Uint8Array(data.buffer, data.byteOffset, data.byteLength),
      length: data.length,
    };
  },
  (zdata: ZDataDict): Uint32Array => {
    const bytes = Buffer.from(zdata.b as Uint8Array);
    return new Uint32Array(bytes.buffer, bytes.byteOffset, zdata.length as number);
  },
  Uint32Array
);

// Int8Array (equivalent to np.int8)
TYPE_REGISTRY.register(
  'Int8Array',
  (data: unknown): ZDataDict | null => {
    if (!(data instanceof Int8Array)) return null;
    return {
      ztype: 'Int8Array',
      b: new Uint8Array(data.buffer, data.byteOffset, data.byteLength),
      length: data.length,
    };
  },
  (zdata: ZDataDict): Int8Array => {
    const bytes = Buffer.from(zdata.b as Uint8Array);
    return new Int8Array(bytes.buffer, bytes.byteOffset, zdata.length as number);
  },
  Int8Array
);

// Int16Array (equivalent to np.int16)
TYPE_REGISTRY.register(
  'Int16Array',
  (data: unknown): ZDataDict | null => {
    if (!(data instanceof Int16Array)) return null;
    return {
      ztype: 'Int16Array',
      b: new Uint8Array(data.buffer, data.byteOffset, data.byteLength),
      length: data.length,
    };
  },
  (zdata: ZDataDict): Int16Array => {
    const bytes = Buffer.from(zdata.b as Uint8Array);
    return new Int16Array(bytes.buffer, bytes.byteOffset, zdata.length as number);
  },
  Int16Array
);

// Int32Array (equivalent to np.int32)
TYPE_REGISTRY.register(
  'Int32Array',
  (data: unknown): ZDataDict | null => {
    if (!(data instanceof Int32Array)) return null;
    return {
      ztype: 'Int32Array',
      b: new Uint8Array(data.buffer, data.byteOffset, data.byteLength),
      length: data.length,
    };
  },
  (zdata: ZDataDict): Int32Array => {
    const bytes = Buffer.from(zdata.b as Uint8Array);
    return new Int32Array(bytes.buffer, bytes.byteOffset, zdata.length as number);
  },
  Int32Array
);
