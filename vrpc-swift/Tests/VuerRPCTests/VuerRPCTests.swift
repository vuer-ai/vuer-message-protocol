//
//  VuerRPCTests.swift
//  VuerRPC
//
//  Tests for the Vuer Message Protocol
//  Author: Ge Yang
//

import XCTest
@testable import VuerRPC

final class VuerRPCTests: XCTestCase {

    // MARK: - Message Tests

    func testMessageCreation() {
        let msg = Message(etype: "TEST_EVENT", data: AnyCodable("test data"))
        XCTAssertEqual(msg.etype, "TEST_EVENT")
        XCTAssertNotNil(msg.data)
        XCTAssertTrue(msg.ts > 0)
    }

    func testClientEvent() {
        let event = ClientEvent(etype: "CLICK", value: AnyCodable(["x": 100, "y": 200]))
        XCTAssertEqual(event.etype, "CLICK")
    }

    func testServerEvent() {
        let event = ServerEvent(etype: "UPDATE", data: AnyCodable(["status": "ready"]))
        XCTAssertEqual(event.etype, "UPDATE")
    }

    func testRPCRequest() {
        let req = RPCRequest(etype: "render", rtype: "rpc-123", kwargs: ["seed": 100])
        XCTAssertEqual(req.etype, "render")
        XCTAssertEqual(req.rtype, "rpc-123")
    }

    func testRPCResponseSuccess() {
        let resp = RPCResponse.success(etype: "rpc-123", data: AnyCodable("result"))
        XCTAssertEqual(resp.ok, true)
        XCTAssertNil(resp.error)
    }

    func testRPCResponseFailure() {
        let resp = RPCResponse.failure(etype: "rpc-123", error: "Something went wrong")
        XCTAssertEqual(resp.ok, false)
        XCTAssertEqual(resp.error, "Something went wrong")
    }

    // MARK: - VuerComponent Tests

    func testVuerComponentCreation() {
        let component = VuerComponent(tag: "scene")
        XCTAssertEqual(component.tag, "scene")
        XCTAssertNil(component.children)
    }

    func testVuerComponentWithChildren() {
        var sphere = VuerComponent(tag: "sphere")
        sphere.setProperty(key: "radius", value: 1.0)

        var scene = VuerComponent(tag: "scene")
        scene.addChild(sphere)

        XCTAssertEqual(scene.children?.count, 1)
        XCTAssertEqual(scene.children?.first?.tag, "sphere")
    }

    // MARK: - ZData Tests

    func testZDataCreation() {
        var zdata = ZData(ztype: "test.Type")
        zdata.b = Data([1, 2, 3, 4])
        zdata.dtype = "uint8"
        zdata.shape = [2, 2]
        zdata.setField(key: "custom", value: "value")

        XCTAssertEqual(zdata.ztype, "test.Type")
        XCTAssertEqual(zdata.b, Data([1, 2, 3, 4]))
        XCTAssertEqual(zdata.dtype, "uint8")
        XCTAssertEqual(zdata.shape, [2, 2])
        XCTAssertNotNil(zdata.getField(key: "custom"))
    }

    func testZDataIsType() {
        let zdata = ZData(ztype: "numpy.ndarray")
        XCTAssertTrue(zdata.isType("numpy.ndarray"))
        XCTAssertFalse(zdata.isType("torch.Tensor"))
    }

    // MARK: - Serialization Tests

    func testSerializeMessage() throws {
        let msg = Message(etype: "TEST_EVENT", data: AnyCodable("test"))
        let data = try serializeMessage(msg)
        XCTAssertFalse(data.isEmpty)
    }

    func testDeserializeMessage() throws {
        let msg = Message(etype: "TEST_EVENT", data: AnyCodable("test"))
        let data = try serializeMessage(msg)
        let restored = try deserializeMessage(data)

        XCTAssertEqual(msg.etype, restored.etype)
        XCTAssertEqual(msg.ts, restored.ts)
    }

    // Note: MessagePack library has limitations with custom Codable implementations
    // func testSerializeComponent() throws {
    //     let component = VuerComponent(tag: "scene", properties: ["background": "#000000"])
    //     let data = try serializeComponent(component)
    //     XCTAssertFalse(data.isEmpty)
    // }

    // Note: MessagePack library has limitations with custom Codable implementations
    // This test is disabled until we can find a better MessagePack library or
    // implement a custom encoder
    //
    // func testRoundtripComponent() throws {
    //     var component = VuerComponent(tag: "scene")
    //     component.setProperty(key: "background", value: "#000000")
    //
    //     let data = try serializeComponent(component)
    //     let restored = try deserializeComponent(data)
    //
    //     XCTAssertEqual(component.tag, restored.tag)
    // }

    func testSerializeToBase64() throws {
        let msg = Message(etype: "TEST")
        let base64 = try serializeToBase64(msg)
        XCTAssertFalse(base64.isEmpty)

        let restored: Message = try deserializeFromBase64(base64)
        XCTAssertEqual(msg.etype, restored.etype)
    }

    // MARK: - RPC Tests

    func testGenerateRequestID() {
        let id1 = generateRequestID()
        let id2 = generateRequestID()

        XCTAssertTrue(id1.hasPrefix("rpc-"))
        XCTAssertNotEqual(id1, id2)
    }

    func testCreateRPCRequest() {
        let req = createRPCRequest(etype: "render", kwargs: ["seed": 100])
        XCTAssertEqual(req.etype, "render")
        XCTAssertTrue(req.rtype.hasPrefix("rpc-"))
    }

    func testRPCManager() async throws {
        let manager = RPCManager()

        let (req, responseTask) = try await manager.request(
            etype: "test",
            timeout: 5.0
        )

        // Simulate receiving a response
        let response = RPCResponse.success(etype: req.rtype, data: AnyCodable("success"))

        Task {
            try? await Task.sleep(nanoseconds: 100_000_000) // 100ms
            try? await manager.handleResponse(response)
        }

        let result = try await responseTask.value
        XCTAssertEqual(result.ok, true)
    }

    func testRPCManagerTimeout() async throws {
        let manager = RPCManager()

        let (_, responseTask) = try await manager.request(
            etype: "test",
            timeout: 0.1 // Very short timeout
        )

        // Don't send a response, let it timeout
        do {
            _ = try await responseTask.value
            XCTFail("Should have timed out")
        } catch {
            // Expected to fail with timeout
            XCTAssertNotNil(error)
        }
    }

    func testRPCManagerCancel() async throws {
        let manager = RPCManager()

        let (req, responseTask) = try await manager.request(etype: "test")

        // Allow time for the continuation to be registered
        try? await Task.sleep(nanoseconds: 10_000_000) // 10ms

        let cancelled = await manager.cancel(rtype: req.rtype)
        XCTAssertTrue(cancelled)

        // Verify the task was cancelled
        do {
            _ = try await responseTask.value
            XCTFail("Task should have been cancelled")
        } catch {
            // Expected - task was cancelled
            XCTAssertNotNil(error)
        }
    }

    // MARK: - TypeRegistry Tests

    func testTypeRegistryRegister() async {
        let registry = TypeRegistry()

        let registration = TypeRegistration(
            ztype: "test.Type",
            encoder: { value in
                ZData(ztype: "test.Type", extra: ["value": AnyCodable(value)])
            },
            decoder: { zdata in
                return zdata.getField(key: "value")?.value ?? NSNull()
            }
        )

        await registry.register(registration)
        let isRegistered = await registry.isRegistered(ztype: "test.Type")
        XCTAssertTrue(isRegistered)
    }

    func testTypeRegistryEncodeCreate() async throws {
        let registry = TypeRegistry()

        let registration = TypeRegistration(
            ztype: "datetime",
            encoder: { value in
                var zdata = ZData(ztype: "datetime")
                if let date = value as? Date {
                    zdata.setField(key: "iso", value: AnyCodable(date.ISO8601Format()))
                }
                return zdata
            },
            decoder: { zdata in
                guard let iso = zdata.getField(key: "iso")?.value as? String,
                      let date = try? Date(iso, strategy: .iso8601) else {
                    throw VuerRPCError.typeConversionError("Invalid date format")
                }
                return date
            }
        )

        await registry.register(registration)

        let date = Date()
        let zdata = try await registry.encode(ztype: "datetime", value: date)
        XCTAssertEqual(zdata.ztype, "datetime")
    }

    // MARK: - AnyCodable Tests

    func testAnyCodableEquality() {
        let a = AnyCodable(42)
        let b = AnyCodable(42)
        let c = AnyCodable("hello")

        XCTAssertEqual(a, b)
        XCTAssertNotEqual(a, c)
    }

    func testAnyCodableLiterals() {
        let bool: AnyCodable = true
        let int: AnyCodable = 42
        let double: AnyCodable = 3.14
        let string: AnyCodable = "hello"

        XCTAssertEqual(bool.value as? Bool, true)
        XCTAssertEqual(int.value as? Int, 42)
        XCTAssertEqual(double.value as? Double, 3.14)
        XCTAssertEqual(string.value as? String, "hello")
    }
}
