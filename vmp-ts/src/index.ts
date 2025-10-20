/**
 * Vuer RPC (vRPC) - TypeScript Implementation
 *
 * A lightweight, cross-language messaging and RPC protocol designed for Vuer and Zaku.
 * Uses MessagePack for efficient binary serialization.
 *
 * @packageDocumentation
 */

// Core types
export type {
  ZDataDict,
  TypeEncoder,
  TypeDecoder,
  TypeChecker,
  VuerComponent,
  Message,
  ClientEvent,
  ServerEvent,
  RPCRequest,
  RPCResponse,
} from './types.js';

// ZData API (main interface)
export { ZData, TYPE_REGISTRY } from './zdata.js';

// Serialization
export {
  serialize,
  serializeMessage,
  serializeComponent,
  serializeToBase64,
} from './serializer.js';

export type { SerializeOptions } from './serializer.js';

// Deserialization
export {
  deserialize,
  deserializeMessage,
  deserializeComponent,
  deserializeFromBase64,
  deserializeWithValidation,
  isMessage,
  isVuerComponent,
  isZData,
} from './deserializer.js';

export type { DeserializeOptions } from './deserializer.js';

// RPC utilities
export {
  generateRequestId,
  createRPCRequest,
  createRPCResponse,
  isRPCRequest,
  isRPCResponse,
  getRequestIdFromResponse,
  RPCManager,
} from './rpc.js';

// React hooks (optional, only imported if react is available)
export {
  useRPC,
  useMessageSubscription,
  useMessageQueue,
  useMessageDeserializer,
  useMessageHandler,
} from './react.js';

export type { MessageTransport } from './react.js';

// Convenience function for ZData.register_type
import { ZData as _ZData } from './zdata.js';
export const registerZDataType = _ZData.register_type.bind(_ZData);
