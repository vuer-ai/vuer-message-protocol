import type { Message, RPCRequest, RPCResponse } from './types.js';

/**
 * Generate a unique request ID for RPC
 */
export function generateRequestId(prefix = 'rpc'): string {
  return `${prefix}-${crypto.randomUUID()}`;
}

/**
 * Create an RPC request message
 *
 * @example
 * ```ts
 * const request = createRPCRequest({
 *   etype: 'CAMERA:main-camera',
 *   args: [100, 200],
 *   kwargs: { duration: 1.5 },
 * });
 * // Returns: { ts: ..., etype: 'CAMERA:main-camera', rtype: 'rpc-...', args: [...], kwargs: {...} }
 * ```
 */
export function createRPCRequest(params: {
  etype: string;
  args?: unknown[];
  kwargs?: Record<string, unknown>;
  requestId?: string;
  data?: unknown;
  value?: unknown;
}): RPCRequest {
  const requestId = params.requestId || generateRequestId();

  return {
    ts: Date.now(),
    etype: params.etype,
    rtype: requestId,
    args: params.args,
    kwargs: params.kwargs,
    data: params.data,
    value: params.value,
  };
}

/**
 * Create an RPC response message
 *
 * @example
 * ```ts
 * const response = createRPCResponse({
 *   request,
 *   data: { success: true },
 * });
 * ```
 */
export function createRPCResponse(params: {
  request: RPCRequest;
  data?: unknown;
  value?: unknown;
  ok?: boolean;
  error?: string | null;
}): RPCResponse {
  return {
    ts: Date.now(),
    etype: params.request.rtype,
    data: params.data,
    value: params.value,
    ok: params.ok ?? true,
    error: params.error ?? null,
  };
}

/**
 * Check if a message is an RPC request
 */
export function isRPCRequest(message: Message): message is RPCRequest {
  return message.rtype !== undefined;
}

/**
 * Check if a message is an RPC response
 */
export function isRPCResponse(message: Message): message is RPCResponse {
  return 'ok' in message || 'error' in message;
}

/**
 * Extract the request ID from an RPC response
 */
export function getRequestIdFromResponse(response: Message): string | undefined {
  return response.etype;
}

/**
 * RPC manager for handling request-response correlation
 */
export class RPCManager {
  private pendingRequests = new Map<
    string,
    {
      resolve: (response: RPCResponse) => void;
      reject: (error: Error) => void;
      timeout?: NodeJS.Timeout;
    }
  >();

  /**
   * Send an RPC request and wait for response
   *
   * @param sender - Function to send the serialized request
   * @param params - RPC request parameters
   * @param timeoutMs - Request timeout in milliseconds (default: 5000)
   * @returns Promise that resolves with the response
   *
   * @example
   * ```ts
   * const manager = new RPCManager();
   * const response = await manager.request(
   *   (data) => websocket.send(data),
   *   {
   *     etype: 'GET_POSITION',
   *     kwargs: { componentKey: 'main-camera' }
   *   }
   * );
   * console.log('Position:', response.data);
   * ```
   */
  request(
    sender: (request: RPCRequest) => void,
    params: {
      etype: string;
      args?: unknown[];
      kwargs?: Record<string, unknown>;
      data?: unknown;
      value?: unknown;
    },
    timeoutMs = 5000
  ): Promise<RPCResponse> {
    const request = createRPCRequest(params);

    return new Promise((resolve, reject) => {
      // Set up timeout
      const timeout = setTimeout(() => {
        this.pendingRequests.delete(request.rtype);
        reject(new Error(`RPC request timeout: ${request.etype}`));
      }, timeoutMs);

      // Store pending request
      this.pendingRequests.set(request.rtype, {
        resolve,
        reject,
        timeout,
      });

      // Send the request
      try {
        sender(request);
      } catch (error) {
        this.pendingRequests.delete(request.rtype);
        clearTimeout(timeout);
        reject(error);
      }
    });
  }

  /**
   * Handle an incoming message
   * If it's an RPC response matching a pending request, resolves the promise
   *
   * @example
   * ```ts
   * websocket.on('message', (data) => {
   *   const message = deserialize(data);
   *   if (manager.handleResponse(message)) {
   *     // Response was handled
   *   } else {
   *     // Handle as regular message
   *   }
   * });
   * ```
   */
  handleResponse(message: Message): boolean {
    const requestId = getRequestIdFromResponse(message);
    if (!requestId) {
      return false;
    }

    const pending = this.pendingRequests.get(requestId);
    if (!pending) {
      return false;
    }

    // Clear timeout
    if (pending.timeout) {
      clearTimeout(pending.timeout);
    }

    // Remove from pending
    this.pendingRequests.delete(requestId);

    // Check for error
    if (isRPCResponse(message) && message.error) {
      pending.reject(new Error(message.error));
    } else {
      pending.resolve(message as RPCResponse);
    }

    return true;
  }

  /**
   * Cancel a pending RPC request
   */
  cancel(requestId: string): void {
    const pending = this.pendingRequests.get(requestId);
    if (pending) {
      if (pending.timeout) {
        clearTimeout(pending.timeout);
      }
      this.pendingRequests.delete(requestId);
      pending.reject(new Error('RPC request cancelled'));
    }
  }

  /**
   * Cancel all pending RPC requests
   */
  cancelAll(): void {
    for (const [, pending] of this.pendingRequests.entries()) {
      if (pending.timeout) {
        clearTimeout(pending.timeout);
      }
      pending.reject(new Error('RPC request cancelled'));
    }
    this.pendingRequests.clear();
  }

  /**
   * Get count of pending requests
   */
  getPendingCount(): number {
    return this.pendingRequests.size;
  }

  /**
   * Get all pending request IDs
   */
  getPendingRequestIds(): string[] {
    return Array.from(this.pendingRequests.keys());
  }
}
