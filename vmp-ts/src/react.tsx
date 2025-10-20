import { useEffect, useRef, useCallback, useMemo, useState } from 'react';
import type { Message, RPCResponse } from './types.js';
import { RPCManager } from './rpc.js';
import { serialize } from './serializer.js';
import { deserialize } from './deserializer.js';

/**
 * WebSocket-like interface for message transport
 */
export interface MessageTransport {
  send: (data: Uint8Array) => void;
  addEventListener?: (event: string, handler: (event: MessageEvent) => void) => void;
  removeEventListener?: (event: string, handler: (event: MessageEvent) => void) => void;
  close?: () => void;
}

/**
 * Hook to manage RPC requests over a message transport
 *
 * @example
 * ```tsx
 * function MyComponent() {
 *   const ws = useWebSocket('ws://localhost:8000');
 *   const rpc = useRPC(ws);
 *
 *   const handleClick = async () => {
 *     const response = await rpc.request({
 *       etype: 'GET_POSITION',
 *       kwargs: { componentKey: 'main-camera' }
 *     });
 *     console.log('Position:', response.data);
 *   };
 *
 *   return <button onClick={handleClick}>Get Position</button>;
 * }
 * ```
 */
export function useRPC(transport: MessageTransport | null) {
  const managerRef = useRef<RPCManager>(new RPCManager());

  const manager = managerRef.current;

  // Clean up on unmount
  useEffect(() => {
    return () => {
      manager.cancelAll();
    };
  }, [manager]);

  const request = useCallback(
    (
      params: {
        etype: string;
        args?: unknown[];
        kwargs?: Record<string, unknown>;
        data?: unknown;
        value?: unknown;
      },
      timeoutMs = 5000
    ): Promise<RPCResponse> => {
      if (!transport) {
        return Promise.reject(new Error('Transport not available'));
      }

      return manager.request(
        (request) => {
          const binary = serialize(request);
          transport.send(binary);
        },
        params,
        timeoutMs
      );
    },
    [transport, manager]
  );

  const handleMessage = useCallback(
    (message: Message) => {
      return manager.handleResponse(message);
    },
    [manager]
  );

  return {
    request,
    handleMessage,
    cancel: manager.cancel.bind(manager),
    cancelAll: manager.cancelAll.bind(manager),
    getPendingCount: manager.getPendingCount.bind(manager),
  };
}

/**
 * Hook to subscribe to messages of a specific event type
 *
 * @example
 * ```tsx
 * function PositionDisplay() {
 *   const [position, setPosition] = useState([0, 0, 0]);
 *
 *   useMessageSubscription('UPDATE', (message) => {
 *     if (message.data?.position) {
 *       setPosition(message.data.position);
 *     }
 *   });
 *
 *   return <div>Position: {position.join(', ')}</div>;
 * }
 * ```
 */
export function useMessageSubscription(
  etype: string | string[],
  handler: (message: Message) => void,
  deps: unknown[] = []
) {
  const etypes = useMemo(
    () => (Array.isArray(etype) ? etype : [etype]),
    [etype]
  );

  const handlerRef = useRef(handler);
  handlerRef.current = handler;

  const filter = useCallback(
    (message: Message) => {
      if (etypes.includes(message.etype)) {
        handlerRef.current(message);
      }
    },
    [etypes, ...deps] // eslint-disable-line react-hooks/exhaustive-deps
  );

  return filter;
}

/**
 * Hook to manage a message queue with automatic serialization
 *
 * @example
 * ```tsx
 * function MessageSender() {
 *   const ws = useWebSocket('ws://localhost:8000');
 *   const { send, queue } = useMessageQueue(ws);
 *
 *   const handleSend = () => {
 *     send({
 *       ts: Date.now(),
 *       etype: 'CLICK',
 *       value: { x: 100, y: 200 }
 *     });
 *   };
 *
 *   return (
 *     <div>
 *       <button onClick={handleSend}>Send</button>
 *       <div>Queue size: {queue.length}</div>
 *     </div>
 *   );
 * }
 * ```
 */
export function useMessageQueue(transport: MessageTransport | null) {
  const [queue, setQueue] = useState<Message[]>([]);

  const send = useCallback(
    (message: Message) => {
      if (!transport) {
        // Queue the message if transport is not available
        setQueue((prev) => [...prev, message]);
        return false;
      }

      try {
        const binary = serialize(message);
        transport.send(binary);
        return true;
      } catch (error) {
        console.error('Failed to send message:', error);
        return false;
      }
    },
    [transport]
  );

  // Flush queue when transport becomes available
  useEffect(() => {
    if (transport && queue.length > 0) {
      queue.forEach((message) => {
        try {
          const binary = serialize(message);
          transport.send(binary);
        } catch (error) {
          console.error('Failed to send queued message:', error);
        }
      });
      setQueue([]);
    }
  }, [transport, queue]);

  const clear = useCallback(() => {
    setQueue([]);
  }, []);

  return {
    send,
    queue,
    clear,
  };
}

/**
 * Hook to deserialize incoming binary messages
 *
 * @example
 * ```tsx
 * function MessageReceiver() {
 *   const [lastMessage, setLastMessage] = useState<Message | null>(null);
 *   const deserializeMessage = useMessageDeserializer();
 *
 *   useEffect(() => {
 *     ws.addEventListener('message', (event) => {
 *       const message = deserializeMessage(event.data);
 *       setLastMessage(message);
 *     });
 *   }, [ws, deserializeMessage]);
 *
 *   return <div>Last: {lastMessage?.etype}</div>;
 * }
 * ```
 */
export function useMessageDeserializer() {
  return useCallback((data: Uint8Array | ArrayBuffer) => {
    const binary = data instanceof ArrayBuffer ? new Uint8Array(data) : data;
    return deserialize<Message>(binary);
  }, []);
}

/**
 * Hook for bidirectional message handling with RPC support
 *
 * @example
 * ```tsx
 * function VuerClient() {
 *   const ws = useWebSocket('ws://localhost:8000');
 *
 *   const { send, rpc, subscribe } = useMessageHandler(ws, (message) => {
 *     console.log('Received:', message);
 *   });
 *
 *   const handleRPC = async () => {
 *     const response = await rpc({
 *       etype: 'GET_STATE',
 *       kwargs: { key: 'scene' }
 *     });
 *     console.log('State:', response.data);
 *   };
 *
 *   return <button onClick={handleRPC}>Get State</button>;
 * }
 * ```
 */
export function useMessageHandler(
  transport: MessageTransport | null,
  onMessage?: (message: Message) => void
) {
  const rpcHook = useRPC(transport);
  const { send } = useMessageQueue(transport);
  const deserializeMessage = useMessageDeserializer();

  // Handle incoming messages
  useEffect(() => {
    if (!transport?.addEventListener) return;

    const handler = (event: MessageEvent) => {
      try {
        const message = deserializeMessage(event.data);

        // Try RPC handler first
        const handled = rpcHook.handleMessage(message);

        // If not an RPC response, call user handler
        if (!handled && onMessage) {
          onMessage(message);
        }
      } catch (error) {
        console.error('Failed to deserialize message:', error);
      }
    };

    transport.addEventListener('message', handler);

    return () => {
      transport.removeEventListener?.('message', handler);
    };
  }, [transport, deserializeMessage, rpcHook, onMessage]);

  return {
    send,
    rpc: rpcHook.request,
    cancelRPC: rpcHook.cancel,
    cancelAllRPC: rpcHook.cancelAll,
  };
}
