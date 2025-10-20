"""
Tests for message types and event creation.
"""

import pytest
from vuer_vrpc import (
    create_client_event,
    create_server_event,
    create_rpc_request,
    create_rpc_response,
    current_timestamp,
)


def test_current_timestamp():
    """Test timestamp generation."""
    ts = current_timestamp()
    assert isinstance(ts, int)
    assert ts > 0


def test_create_client_event():
    """Test creating client events."""
    # Basic event
    event = create_client_event("CLICK", value={"x": 100, "y": 200})

    assert event["etype"] == "CLICK"
    assert event["value"] == {"x": 100, "y": 200}
    assert "ts" in event
    assert isinstance(event["ts"], int)

    # Event with key
    event_with_key = create_client_event("UPDATE", value=42, key="node1")
    assert event_with_key["key"] == "node1"

    # Event with rtype (RPC)
    rpc_event = create_client_event("RPC", value={}, rtype="RESPONSE")
    assert rpc_event["rtype"] == "RESPONSE"

    # Event with custom timestamp
    ts = 1234567890
    event_ts = create_client_event("TEST", ts=ts)
    assert event_ts["ts"] == ts


def test_create_server_event():
    """Test creating server events."""
    data = {"nodes": [{"key": "box1", "tag": "mesh"}]}
    event = create_server_event("UPDATE", data)

    assert event["etype"] == "UPDATE"
    assert event["data"] == data
    assert "ts" in event

    # With custom timestamp
    ts = 9876543210
    event_ts = create_server_event("SET", {"tag": "scene"}, ts=ts)
    assert event_ts["ts"] == ts


def test_create_rpc_request():
    """Test creating RPC requests."""
    # Basic RPC
    request = create_rpc_request(
        "COMPUTE",
        "RESULT",
        args=[1, 2, 3],
        kwargs={"operation": "sum"}
    )

    assert request["etype"] == "COMPUTE"
    assert request["rtype"] == "RESULT"
    assert request["args"] == [1, 2, 3]
    assert request["kwargs"] == {"operation": "sum"}
    assert "ts" in request

    # RPC with UUID
    request_uuid = create_rpc_request(
        "RENDER",
        "RENDER_RESULT",
        uuid="req-123"
    )
    assert request_uuid["uuid"] == "req-123"


def test_create_rpc_response():
    """Test creating RPC responses."""
    # Success response with data
    response = create_rpc_response(
        "RESULT",
        data={"value": 42},
        ok=True
    )

    assert response["etype"] == "RESULT"
    assert response["data"] == {"value": 42}
    assert response["ok"] is True
    assert response["error"] is None

    # Error response
    error_response = create_rpc_response(
        "ERROR",
        ok=False,
        error="Computation failed"
    )

    assert error_response["ok"] is False
    assert error_response["error"] == "Computation failed"

    # Response with value (client-side)
    client_response = create_rpc_response(
        "CLIENT_RESULT",
        value={"status": "done"}
    )

    assert client_response["value"] == {"status": "done"}
