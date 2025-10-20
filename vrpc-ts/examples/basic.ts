/**
 * Basic usage example for vmp-ts
 */

import {
  serialize,
  deserialize,
  createRPCRequest,
  createRPCResponse,
  registerZDataType,
  type Message,
} from '../src/index.js';

// Example 1: Basic message serialization
console.log('Example 1: Basic message serialization');
const message: Message = {
  ts: Date.now(),
  etype: 'UPDATE',
  data: {
    position: [1, 2, 3],
    rotation: [0, 0, 0],
  },
};

const binary = serialize(message);
console.log('Serialized size:', binary.length, 'bytes');

const decoded = deserialize<Message>(binary);
console.log('Decoded message:', decoded);
console.log('');

// Example 2: RPC request/response
console.log('Example 2: RPC request/response');
const request = createRPCRequest({
  etype: 'GET_POSITION',
  kwargs: { componentKey: 'main-camera' },
});
console.log('RPC Request:', request);

const response = createRPCResponse({
  request,
  data: { position: [10, 20, 30] },
});
console.log('RPC Response:', response);
console.log('');

// Example 3: Custom ZData type
console.log('Example 3: Custom ZData type');
registerZDataType({
  ztype: 'datetime',
  encode: (value: unknown) => {
    if (value instanceof Date) {
      return {
        ztype: 'datetime',
        iso: value.toISOString(),
      };
    }
    return null;
  },
  decode: (zdata) => {
    if (zdata.ztype === 'datetime' && 'iso' in zdata) {
      return new Date(zdata.iso as string);
    }
    return null;
  },
});

const messageWithDate: Message = {
  ts: Date.now(),
  etype: 'EVENT',
  data: {
    timestamp: new Date('2025-01-15T12:00:00Z'),
  },
};

const binaryWithDate = serialize(messageWithDate);
const decodedWithDate = deserialize<Message>(binaryWithDate);
console.log('Message with custom Date type:', decodedWithDate);
console.log('');

// Example 4: VuerComponent tree
console.log('Example 4: VuerComponent tree');
const scene = {
  tag: 'scene',
  children: [
    {
      tag: 'box',
      position: [0, 0, 0],
      color: '#ff0000',
      children: [],
    },
    {
      tag: 'sphere',
      position: [1, 1, 1],
      radius: 0.5,
      children: [],
    },
  ],
};

const sceneBinary = serialize(scene);
const decodedScene = deserialize(sceneBinary);
console.log('Serialized scene:', JSON.stringify(decodedScene, null, 2));
