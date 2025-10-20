"""
Basic usage examples for vmp-py.

Demonstrates:
- ZData encoding/decoding
- Event creation
- Serialization
- Custom type registration
"""

import numpy as np
from vuer_vrpc import (
    ZData,
    MessagePackSerializer,
    set_event,
    add_event,
    update_event,
    create_rpc_request,
    create_rpc_response,
)


def example_zdata():
    """Example: Using ZData to encode numpy arrays."""
    print("\n=== ZData Encoding Example ===")

    # Create a numpy array
    arr = np.array([[1, 2, 3], [4, 5, 6]])
    print(f"Original array:\n{arr}")

    # Encode to ZData format
    encoded = ZData.encode(arr)
    print(f"\nEncoded: {encoded.keys()}")
    print(f"Type: {encoded['ztype']}")
    print(f"Shape: {encoded['shape']}")
    print(f"Dtype: {encoded['dtype']}")

    # Decode back to numpy
    decoded = ZData.decode(encoded)
    print(f"\nDecoded array:\n{decoded}")

    assert np.array_equal(arr, decoded)
    print("✓ Round-trip successful!")


def example_events():
    """Example: Creating scene graph events."""
    print("\n=== Event Creation Example ===")

    # SET event to initialize scene
    scene = set_event({
        "tag": "scene",
        "key": "root",
        "bgColor": [0.1, 0.1, 0.1]
    })
    print(f"SET event: {scene['etype']}")
    print(f"  Timestamp: {scene['ts']}")
    print(f"  Data: {scene['data']}")

    # ADD event to add nodes
    nodes = add_event([
        {"tag": "mesh", "key": "box1", "position": [0, 0, 0]},
        {"tag": "mesh", "key": "box2", "position": [1, 1, 1]},
    ])
    print(f"\nADD event: {nodes['etype']}")
    print(f"  Number of nodes: {len(nodes['data']['nodes'])}")

    # UPDATE event to modify nodes
    updates = update_event([
        {"key": "box1", "position": [2, 0, 0]},
    ])
    print(f"\nUPDATE event: {updates['etype']}")


def example_serialization():
    """Example: Serializing events with numpy arrays."""
    print("\n=== Serialization Example ===")

    serializer = MessagePackSerializer(greedy=True)

    # Create event with numpy array
    arr = np.array([1.0, 2.0, 3.0])
    event = set_event({
        "tag": "scene",
        "data": arr,
        "metadata": "example"
    })

    print(f"Event with numpy array:")
    print(f"  Type: {type(event['data']['data'])}")

    # Serialize to binary
    binary = serializer.encode(event)
    print(f"\nSerialized to {len(binary)} bytes")

    # Deserialize
    decoded = serializer.decode(binary)
    print(f"\nDeserialized event:")
    print(f"  Type: {decoded['etype']}")
    print(f"  Data type: {type(decoded['data']['data'])}")
    print(f"  Array: {decoded['data']['data']}")

    assert np.array_equal(event['data']['data'], decoded['data']['data'])
    print("✓ Serialization round-trip successful!")


def example_rpc():
    """Example: Creating RPC messages."""
    print("\n=== RPC Example ===")

    # Client creates request
    request = create_rpc_request(
        etype="COMPUTE",
        rtype="COMPUTE_RESULT",
        args=[1, 2, 3],
        kwargs={"operation": "sum"},
        uuid="req-12345"
    )

    print(f"RPC Request:")
    print(f"  Event type: {request['etype']}")
    print(f"  Response type: {request['rtype']}")
    print(f"  Args: {request['args']}")
    print(f"  Kwargs: {request['kwargs']}")
    print(f"  UUID: {request['uuid']}")

    # Server creates response
    response = create_rpc_response(
        etype="COMPUTE_RESULT",
        data={"result": 6},
        ok=True,
        error=None
    )

    print(f"\nRPC Response:")
    print(f"  Event type: {response['etype']}")
    print(f"  Result: {response['data']}")
    print(f"  Status: {'Success' if response['ok'] else 'Failed'}")


def example_custom_type():
    """Example: Registering custom types."""
    print("\n=== Custom Type Registration Example ===")

    # Define custom type
    class Point:
        def __init__(self, x, y):
            self.x = x
            self.y = y

        def __repr__(self):
            return f"Point({self.x}, {self.y})"

    # Define encoder and decoder
    def encode_point(p):
        return {
            "ztype": "custom.Point",
            "b": f"{p.x},{p.y}".encode()
        }

    def decode_point(zdata):
        x, y = map(float, zdata["b"].decode().split(","))
        return Point(x, y)

    # Register the type
    ZData.register_type(
        "custom.Point",
        encode_point,
        decode_point,
        type_class=Point
    )

    print("Registered custom type: Point")

    # Use the custom type
    point = Point(3.14, 2.71)
    print(f"\nOriginal point: {point}")

    # Encode
    encoded = ZData.encode(point)
    print(f"Encoded: {encoded}")

    # Decode
    decoded = ZData.decode(encoded)
    print(f"Decoded: {decoded}")

    # Use in serialization
    serializer = MessagePackSerializer(greedy=True)
    data = {"point": point, "name": "example"}

    binary = serializer.encode(data)
    result = serializer.decode(binary)

    print(f"\nAfter full serialization:")
    print(f"  Point: {result['point']}")
    print(f"  Name: {result['name']}")
    print("✓ Custom type works!")


def main():
    """Run all examples."""
    print("=" * 60)
    print("VMP-PY Basic Usage Examples")
    print("=" * 60)

    example_zdata()
    example_events()
    example_serialization()
    example_rpc()
    example_custom_type()

    print("\n" + "=" * 60)
    print("All examples completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
