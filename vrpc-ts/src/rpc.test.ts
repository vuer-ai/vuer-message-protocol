import { describe, it, expect, beforeEach, vi } from 'vitest';
import {
  createRPCRequest,
  createRPCResponse,
  isRPCRequest,
  isRPCResponse,
  RPCManager,
} from './rpc.js';
import type { RPCRequest, RPCResponse } from './types.js';

describe('RPC', () => {
  describe('createRPCRequest', () => {
    it('should create a valid RPC request', () => {
      const request = createRPCRequest({
        etype: 'GET_POSITION',
        kwargs: { componentKey: 'main-camera' },
      });

      expect(request.etype).toBe('GET_POSITION');
      expect(request.rtype).toBeDefined();
      expect(request.rtype).toMatch(/^rpc-/);
      expect(request.kwargs).toEqual({ componentKey: 'main-camera' });
      expect(request.ts).toBeTypeOf('number');
    });

    it('should accept custom request ID', () => {
      const request = createRPCRequest({
        etype: 'GET_STATE',
        requestId: 'custom-id',
      });

      expect(request.rtype).toBe('custom-id');
    });

    it('should handle args and kwargs', () => {
      const request = createRPCRequest({
        etype: 'RENDER',
        args: [100, 200],
        kwargs: { quality: 'high' },
      });

      expect(request.args).toEqual([100, 200]);
      expect(request.kwargs).toEqual({ quality: 'high' });
    });
  });

  describe('createRPCResponse', () => {
    it('should create a valid RPC response', () => {
      const request = createRPCRequest({
        etype: 'GET_POSITION',
      });

      const response = createRPCResponse({
        request,
        data: { position: [1, 2, 3] },
      });

      expect(response.etype).toBe(request.rtype);
      expect(response.data).toEqual({ position: [1, 2, 3] });
      expect(response.ok).toBe(true);
      expect(response.error).toBeNull();
    });

    it('should handle errors', () => {
      const request = createRPCRequest({
        etype: 'GET_STATE',
      });

      const response = createRPCResponse({
        request,
        ok: false,
        error: 'Not found',
      });

      expect(response.ok).toBe(false);
      expect(response.error).toBe('Not found');
    });
  });

  describe('Type guards', () => {
    it('should identify RPC requests', () => {
      const request = createRPCRequest({
        etype: 'TEST',
      });

      expect(isRPCRequest(request)).toBe(true);
    });

    it('should identify RPC responses', () => {
      const request = createRPCRequest({ etype: 'TEST' });
      const response = createRPCResponse({
        request,
        data: {},
      });

      expect(isRPCResponse(response)).toBe(true);
    });

    it('should reject non-RPC messages', () => {
      const message = {
        ts: Date.now(),
        etype: 'UPDATE',
        data: {},
      };

      expect(isRPCRequest(message)).toBe(false);
      expect(isRPCResponse(message)).toBe(false);
    });
  });

  describe('RPCManager', () => {
    let manager: RPCManager;

    beforeEach(() => {
      manager = new RPCManager();
    });

    it('should handle successful RPC request-response', async () => {
      const sender = vi.fn((request: RPCRequest) => {
        // Simulate async response
        setTimeout(() => {
          const response = createRPCResponse({
            request,
            data: { result: 'success' },
          });
          manager.handleResponse(response);
        }, 10);
      });

      const responsePromise = manager.request(
        sender,
        { etype: 'TEST' },
        1000
      );

      expect(sender).toHaveBeenCalledOnce();
      expect(manager.getPendingCount()).toBe(1);

      const response = await responsePromise;

      expect(response.data).toEqual({ result: 'success' });
      expect(manager.getPendingCount()).toBe(0);
    });

    it('should timeout if no response', async () => {
      const sender = vi.fn();

      const responsePromise = manager.request(
        sender,
        { etype: 'TEST' },
        100 // short timeout
      );

      await expect(responsePromise).rejects.toThrow('RPC request timeout');
      expect(manager.getPendingCount()).toBe(0);
    });

    it('should handle multiple concurrent requests', async () => {
      const responses = new Map<string, RPCResponse>();

      const sender = vi.fn((request: RPCRequest) => {
        setTimeout(() => {
          const response = createRPCResponse({
            request,
            data: { requestId: request.rtype },
          });
          responses.set(request.rtype, response);
          manager.handleResponse(response);
        }, 10);
      });

      const promise1 = manager.request(sender, { etype: 'TEST1' }, 1000);
      const promise2 = manager.request(sender, { etype: 'TEST2' }, 1000);
      const promise3 = manager.request(sender, { etype: 'TEST3' }, 1000);

      expect(manager.getPendingCount()).toBe(3);

      const [response1, response2, response3] = await Promise.all([
        promise1,
        promise2,
        promise3,
      ]);

      expect(response1.data).toBeDefined();
      expect(response2.data).toBeDefined();
      expect(response3.data).toBeDefined();
      expect(manager.getPendingCount()).toBe(0);
    });

    it('should handle error responses', async () => {
      const sender = vi.fn((request: RPCRequest) => {
        setTimeout(() => {
          const response = createRPCResponse({
            request,
            ok: false,
            error: 'Something went wrong',
          });
          manager.handleResponse(response);
        }, 10);
      });

      const responsePromise = manager.request(sender, { etype: 'TEST' }, 1000);

      await expect(responsePromise).rejects.toThrow('Something went wrong');
    });

    it('should cancel pending requests', async () => {
      const sender = vi.fn();
      const request = createRPCRequest({ etype: 'TEST' });

      const responsePromise = manager.request(
        (req) => {
          sender(req);
          manager.cancel(req.rtype);
        },
        { etype: 'TEST', requestId: request.rtype },
        1000
      );

      await expect(responsePromise).rejects.toThrow('RPC request cancelled');
    });

    it('should cancel all pending requests', async () => {
      const sender = vi.fn();

      const promise1 = manager.request(sender, { etype: 'TEST1' }, 1000);
      const promise2 = manager.request(sender, { etype: 'TEST2' }, 1000);

      expect(manager.getPendingCount()).toBe(2);

      manager.cancelAll();

      await expect(promise1).rejects.toThrow('RPC request cancelled');
      await expect(promise2).rejects.toThrow('RPC request cancelled');
      expect(manager.getPendingCount()).toBe(0);
    });

    it('should ignore non-matching responses', () => {
      const response = {
        ts: Date.now(),
        etype: 'unknown-id',
        data: {},
        ok: true,
        error: null,
      };

      const handled = manager.handleResponse(response);
      expect(handled).toBe(false);
    });
  });
});
