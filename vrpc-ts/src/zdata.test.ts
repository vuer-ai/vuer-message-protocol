import { describe, it, expect, beforeEach } from 'vitest';
import { ZData, TYPE_REGISTRY } from './zdata.js';
import { serialize } from './serializer.js';
import { deserialize } from './deserializer.js';

describe('ZData', () => {
  describe('TypedArray encoding/decoding', () => {
    it('should encode and decode Float32Array', () => {
      const arr = new Float32Array([1, 2, 3, 4, 5]);
      const encoded = ZData.encode(arr);

      expect(ZData.is_zdata(encoded)).toBe(true);
      expect(ZData.get_ztype(encoded)).toBe('Float32Array');

      const decoded = ZData.decode(encoded);
      expect(decoded).toBeInstanceOf(Float32Array);
      expect(Array.from(decoded as Float32Array)).toEqual([1, 2, 3, 4, 5]);
    });

    it('should encode and decode Uint8Array', () => {
      const arr = new Uint8Array([255, 128, 0, 64, 32]);
      const encoded = ZData.encode(arr);

      expect(ZData.get_ztype(encoded)).toBe('Uint8Array');

      const decoded = ZData.decode(encoded) as Uint8Array;
      expect(decoded).toBeInstanceOf(Uint8Array);
      expect(Array.from(decoded)).toEqual([255, 128, 0, 64, 32]);
    });

    it('should encode and decode Uint16Array', () => {
      const arr = new Uint16Array([1000, 2000, 3000]);
      const encoded = ZData.encode(arr);

      const decoded = ZData.decode(encoded) as Uint16Array;
      expect(decoded).toBeInstanceOf(Uint16Array);
      expect(Array.from(decoded)).toEqual([1000, 2000, 3000]);
    });

    it('should encode and decode Uint32Array', () => {
      const arr = new Uint32Array([100000, 200000, 300000]);
      const encoded = ZData.encode(arr);

      const decoded = ZData.decode(encoded) as Uint32Array;
      expect(decoded).toBeInstanceOf(Uint32Array);
      expect(Array.from(decoded)).toEqual([100000, 200000, 300000]);
    });
  });

  describe('is_zdata and get_ztype', () => {
    it('should detect ZData objects', () => {
      const arr = new Float32Array([1, 2, 3]);
      const encoded = ZData.encode(arr);

      expect(ZData.is_zdata(encoded)).toBe(true);
      expect(ZData.is_zdata(arr)).toBe(false);
      expect(ZData.is_zdata({ some: 'dict' })).toBe(false);
      expect(ZData.is_zdata([1, 2, 3])).toBe(false);
    });

    it('should get ztype from encoded data', () => {
      const arr = new Float32Array([1, 2, 3]);
      const encoded = ZData.encode(arr);

      expect(ZData.get_ztype(encoded)).toBe('Float32Array');
      expect(ZData.get_ztype(arr)).toBeUndefined();
      expect(ZData.get_ztype({ some: 'dict' })).toBeUndefined();
    });
  });

  describe('passthrough for unsupported types', () => {
    it('should pass through primitives unchanged', () => {
      expect(ZData.encode(42)).toBe(42);
      expect(ZData.encode('hello')).toBe('hello');
      expect(ZData.encode([1, 2, 3])).toEqual([1, 2, 3]);
      expect(ZData.encode({ key: 'value' })).toEqual({ key: 'value' });
    });

    it('should pass through non-ZData on decode', () => {
      expect(ZData.decode(42)).toBe(42);
      expect(ZData.decode('hello')).toBe('hello');
    });
  });

  describe('custom type registration', () => {
    // Define a custom type
    class Point {
      constructor(
        public x: number,
        public y: number
      ) {}
    }

    beforeEach(() => {
      // Clear any previously registered Point type
      // (TypeRegistry doesn't have unregister, so we just re-register)
    });

    it('should register and encode/decode custom type', () => {
      // Register the type
      ZData.register_type(
        'custom.Point',
        (p) => {
          if (p instanceof Point) {
            const text = `${p.x},${p.y}`;
            return {
              ztype: 'custom.Point',
              b: new TextEncoder().encode(text),
            };
          }
          return null;
        },
        (zdata) => {
          const text = new TextDecoder().decode(zdata.b as Uint8Array);
          const [x, y] = text.split(',').map(Number);
          return new Point(x, y);
        },
        Point
      );

      // Test encoding and decoding
      const point = new Point(3.14, 2.71);
      const encoded = ZData.encode(point);

      expect(ZData.get_ztype(encoded)).toBe('custom.Point');
      expect(ZData.is_zdata(encoded)).toBe(true);

      const decoded = ZData.decode(encoded) as Point;
      expect(decoded).toBeInstanceOf(Point);
      expect(decoded.x).toBe(3.14);
      expect(decoded.y).toBe(2.71);
    });

    it('should register custom type with type checker', () => {
      class Vector {
        constructor(
          public x: number,
          public y: number,
          public z: number
        ) {}
      }

      function isVector(obj: unknown): boolean {
        return (
          typeof obj === 'object' &&
          obj !== null &&
          'x' in obj &&
          'y' in obj &&
          'z' in obj
        );
      }

      ZData.register_type(
        'custom.Vector',
        (v) => {
          if (isVector(v)) {
            const vec = v as Vector;
            const text = `${vec.x},${vec.y},${vec.z}`;
            return {
              ztype: 'custom.Vector',
              b: new TextEncoder().encode(text),
            };
          }
          return null;
        },
        (zdata) => {
          const text = new TextDecoder().decode(zdata.b as Uint8Array);
          const [x, y, z] = text.split(',').map(Number);
          return new Vector(x, y, z);
        },
        undefined, // no type class
        isVector // type checker
      );

      const vec = new Vector(1.0, 2.0, 3.0);
      const encoded = ZData.encode(vec);
      expect(ZData.get_ztype(encoded)).toBe('custom.Vector');

      const decoded = ZData.decode(encoded) as Vector;
      expect(decoded.x).toBe(1.0);
      expect(decoded.y).toBe(2.0);
      expect(decoded.z).toBe(3.0);
    });
  });

  describe('unknown ztype throws error', () => {
    it('should throw TypeError for unknown ztype', () => {
      const fakeZData = {
        ztype: 'unknown.Type',
        b: new Uint8Array([1, 2, 3]),
      };

      expect(() => ZData.decode(fakeZData)).toThrow(TypeError);
      expect(() => ZData.decode(fakeZData)).toThrow('Unknown ZData type');
    });
  });

  describe('identity function', () => {
    it('should wrap data with ztype tag', () => {
      const data = { x: 1, y: 2 };
      const tagged = ZData.identity('custom.MyType', data);

      expect(tagged.ztype).toBe('custom.MyType');
      expect(tagged.data).toEqual(data);
      expect(ZData.is_zdata(tagged)).toBe(true);
    });

    it('should work with various data types', () => {
      const tagged1 = ZData.identity('sphere', { radius: 1 });
      const tagged2 = ZData.identity('box', { size: [1, 2, 3] });
      const tagged3 = ZData.identity('number', 42);

      expect(tagged1.ztype).toBe('sphere');
      expect(tagged2.ztype).toBe('box');
      expect(tagged3.ztype).toBe('number');
    });
  });

  describe('integration with serializer', () => {
    it('should serialize and deserialize TypedArrays', () => {
      const data = {
        vertices: new Float32Array([1, 2, 3, 4, 5, 6]),
        indices: new Uint16Array([0, 1, 2, 3, 4, 5]),
        colors: new Uint8Array([255, 0, 0, 0, 255, 0]),
      };

      const binary = serialize(data);
      const decoded = deserialize(binary);

      expect(decoded.vertices).toBeInstanceOf(Float32Array);
      expect(decoded.indices).toBeInstanceOf(Uint16Array);
      expect(decoded.colors).toBeInstanceOf(Uint8Array);

      expect(Array.from(decoded.vertices as Float32Array)).toEqual([
        1, 2, 3, 4, 5, 6,
      ]);
      expect(Array.from(decoded.indices as Uint16Array)).toEqual([
        0, 1, 2, 3, 4, 5,
      ]);
      expect(Array.from(decoded.colors as Uint8Array)).toEqual([
        255, 0, 0, 0, 255, 0,
      ]);
    });
  });

  describe('list_types', () => {
    it('should list all registered types', () => {
      const types = ZData.list_types();

      expect(types).toContain('Float32Array');
      expect(types).toContain('Float64Array');
      expect(types).toContain('Uint8Array');
      expect(types).toContain('Uint16Array');
      expect(types).toContain('Uint32Array');
      expect(types).toContain('Int8Array');
      expect(types).toContain('Int16Array');
      expect(types).toContain('Int32Array');
    });
  });
});
