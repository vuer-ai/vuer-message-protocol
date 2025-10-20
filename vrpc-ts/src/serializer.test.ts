import { describe, it, expect } from 'vitest';
import { serialize, serializeMessage } from './serializer.js';
import { deserialize } from './deserializer.js';
import type { Message } from './types.js';

describe('Serializer', () => {
  it('should serialize and deserialize a simple message', () => {
    const message: Message = {
      ts: Date.now(),
      etype: 'UPDATE',
      data: { position: [1, 2, 3] },
    };

    const binary = serialize(message);
    const decoded = deserialize<Message>(binary);

    expect(decoded.etype).toBe('UPDATE');
    expect(decoded.data).toEqual({ position: [1, 2, 3] });
  });

  it('should handle nested objects', () => {
    const data = {
      level1: {
        level2: {
          level3: {
            value: 'deep',
            array: [1, 2, 3],
          },
        },
      },
    };

    const binary = serialize(data);
    const decoded = deserialize(binary);

    expect(decoded).toEqual(data);
  });

  it('should handle arrays of objects', () => {
    const data = {
      components: [
        { tag: 'box', position: [0, 0, 0] },
        { tag: 'sphere', position: [1, 1, 1] },
      ],
    };

    const binary = serialize(data);
    const decoded = deserialize(binary);

    expect(decoded).toEqual(data);
  });

  it('should preserve Uint8Array in ZData', () => {
    const zdata = {
      ztype: 'image',
      b: new Uint8Array([1, 2, 3, 4]),
    };

    const binary = serialize(zdata);
    const decoded = deserialize(binary) as typeof zdata;

    expect(decoded.ztype).toBe('image');
    // msgpackr deserializes Uint8Array as Buffer in Node.js
    expect(Buffer.from(decoded.b)).toEqual(Buffer.from([1, 2, 3, 4]));
  });

  it('should handle null and undefined', () => {
    const data = {
      nullValue: null,
      undefinedValue: undefined,
      normalValue: 'hello',
    };

    const binary = serialize(data);
    const decoded = deserialize(binary);

    // msgpack converts undefined to null during serialization
    expect(decoded).toEqual({
      nullValue: null,
      undefinedValue: null,
      normalValue: 'hello',
    });
  });

  it('should serialize RPC messages', () => {
    const message: Message = {
      ts: Date.now(),
      etype: 'CAMERA:main',
      rtype: 'rpc-123',
      kwargs: { duration: 1.5 },
    };

    const binary = serializeMessage(message);
    const decoded = deserialize<Message>(binary);

    expect(decoded.etype).toBe('CAMERA:main');
    expect(decoded.rtype).toBe('rpc-123');
    expect(decoded.kwargs).toEqual({ duration: 1.5 });
  });
});
