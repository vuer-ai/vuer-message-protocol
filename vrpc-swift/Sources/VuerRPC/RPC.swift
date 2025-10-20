//
//  RPC.swift
//  VuerRPC
//
//  RPC (Remote Procedure Call) utilities
//  Author: Ge Yang
//

import Foundation

/// Generate a unique request ID
public func generateRequestID() -> String {
    return "rpc-\(UUID().uuidString.lowercased())"
}

/// Create an RPC request
public func createRPCRequest(
    etype: String,
    args: [AnyCodable]? = nil,
    kwargs: [String: AnyCodable]? = nil
) -> RPCRequest {
    let rtype = generateRequestID()
    return RPCRequest(etype: etype, rtype: rtype, args: args, kwargs: kwargs)
}

/// Create an RPC response
public func createRPCResponse(etype: String, result: Result<AnyCodable, Error>) -> RPCResponse {
    switch result {
    case .success(let data):
        return .success(etype: etype, data: data)
    case .failure(let error):
        return .failure(etype: etype, error: error.localizedDescription)
    }
}

/// RPC Manager for handling request-response correlation
///
/// This manager maintains a registry of pending RPC requests and
/// correlates responses back to the original callers using Swift async/await.
public actor RPCManager {
    private var pending: [String: CheckedContinuation<RPCResponse, Error>] = [:]

    public init() {}

    /// Send an RPC request and wait for a response
    ///
    /// - Parameters:
    ///   - etype: The event type (method name)
    ///   - args: Optional positional arguments
    ///   - kwargs: Optional keyword arguments
    ///   - timeout: Maximum time to wait for response (in seconds)
    /// - Returns: A tuple of (RPCRequest, response Task)
    public func request(
        etype: String,
        args: [AnyCodable]? = nil,
        kwargs: [String: AnyCodable]? = nil,
        timeout: TimeInterval = 5.0
    ) async throws -> (RPCRequest, Task<RPCResponse, Error>) {
        let req = createRPCRequest(etype: etype, args: args, kwargs: kwargs)
        let rtype = req.rtype

        let responseTask = Task<RPCResponse, Error> {
            try await withCheckedThrowingContinuation { continuation in
                Task {
                    await self.registerPending(rtype: rtype, continuation: continuation)
                }
            }
        }

        // Set up timeout
        Task {
            try? await Task.sleep(nanoseconds: UInt64(timeout * 1_000_000_000))
            if await self.isPending(rtype: rtype) {
                await self.cancel(rtype: rtype)
            }
        }

        return (req, responseTask)
    }

    /// Handle an incoming RPC response
    ///
    /// This should be called when a response is received to correlate
    /// it back to the original request.
    public func handleResponse(_ response: RPCResponse) throws {
        guard let continuation = pending.removeValue(forKey: response.etype) else {
            throw VuerRPCError.rpcError("No pending request for response type: \(response.etype)")
        }
        continuation.resume(returning: response)
    }

    /// Cancel a pending request
    @discardableResult
    public func cancel(rtype: String) -> Bool {
        if let continuation = pending.removeValue(forKey: rtype) {
            continuation.resume(throwing: VuerRPCError.rpcTimeout("Request timed out"))
            return true
        }
        return false
    }

    /// Get the number of pending requests
    public func pendingCount() -> Int {
        return pending.count
    }

    /// Clear all pending requests
    public func clear() {
        for (_, continuation) in pending {
            continuation.resume(throwing: VuerRPCError.rpcError("RPC manager cleared"))
        }
        pending.removeAll()
    }

    // MARK: - Private Methods

    private func registerPending(rtype: String, continuation: CheckedContinuation<RPCResponse, Error>) {
        pending[rtype] = continuation
    }

    private func isPending(rtype: String) -> Bool {
        return pending.keys.contains(rtype)
    }
}
