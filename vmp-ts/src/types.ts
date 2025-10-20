/**
 * Core type definitions for VMP (Vuer Message Protocol)
 */

/**
 * ZData dictionary - encoded binary data with type information
 */
export interface ZDataDict {
  ztype: string;
  b?: Uint8Array | ArrayBuffer;
  dtype?: string;
  shape?: number[];
  [key: string]: unknown;
}

/**
 * Type encoder function - converts data to ZDataDict format
 */
export type TypeEncoder<T = unknown> = (data: T) => ZDataDict | null;

/**
 * Type decoder function - converts ZDataDict back to original type
 */
export type TypeDecoder<T = unknown> = (zdata: ZDataDict) => T | null;

/**
 * Type checker function - determines if a value is of a specific type
 */
export type TypeChecker = (data: unknown) => boolean;

/**
 * Vuer Component Schema
 * Represents a component in the Vuer scene graph
 */
export interface VuerComponent {
  tag: string;
  children?: VuerComponent[];
  [key: string]: unknown;
}

/**
 * Generic message envelope with all possible fields
 */
export interface Message {
  ts: number; // timestamp
  etype: string; // event type or queue name
  rtype?: string; // response type (RPC)
  args?: unknown[]; // positional arguments for RPC
  kwargs?: Record<string, unknown>; // keyword arguments
  data?: unknown; // server payload
  value?: unknown; // client payload
}

/**
 * Client-to-server event with value payload
 */
export interface ClientEvent {
  ts: number; // timestamp
  etype: string; // event type
  rtype?: string; // response type (RPC)
  value: unknown; // client payload
}

/**
 * Server-to-client event with data payload
 */
export interface ServerEvent {
  ts: number; // timestamp
  etype: string; // event type
  data: unknown; // server payload
}

/**
 * RPC Request message
 */
export interface RPCRequest extends Message {
  rtype: string; // required for RPC
  args?: unknown[];
  kwargs?: Record<string, unknown>;
}

/**
 * RPC Response message
 */
export interface RPCResponse extends Message {
  ok?: boolean;
  error?: string | null;
}
