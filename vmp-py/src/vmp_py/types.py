"""
Message types and envelopes for Vuer Message Protocol.

Defines the core message structures used for communication between
clients and servers in the Vuer ecosystem.
"""

from typing import Any, Optional, TypedDict, Union
from typing_extensions import NotRequired
import time


class Message(TypedDict, total=False):
    """
    Base message envelope with all possible fields.

    Used for generic message passing in both directions.
    """
    ts: int  # Timestamp in milliseconds
    etype: str  # Event type or queue name
    rtype: NotRequired[str]  # Response type (for RPC)
    args: NotRequired[list[Any]]  # Positional arguments for RPC
    kwargs: NotRequired[dict[str, Any]]  # Keyword arguments
    data: NotRequired[Any]  # Server payload
    value: NotRequired[Any]  # Client payload
    key: NotRequired[str]  # Optional entity identifier
    uuid: NotRequired[str]  # Optional request correlation ID


class ClientEvent(TypedDict, total=False):
    """
    Client-to-server event with value payload.

    Used when clients send data or make requests to the server.
    """
    ts: int  # Timestamp in milliseconds
    etype: str  # Event type
    rtype: NotRequired[str]  # Response type (for RPC)
    value: NotRequired[Any]  # Client payload
    key: NotRequired[str]  # Optional entity identifier


class ServerEvent(TypedDict, total=False):
    """
    Server-to-client event with data payload.

    Used when servers send data or respond to client requests.
    """
    ts: int  # Timestamp in milliseconds
    etype: str  # Event type
    data: Any  # Server payload


class RPCRequest(TypedDict, total=False):
    """
    RPC request with response type specified.

    Contains optional args and kwargs fields for function parameters.
    """
    ts: int  # Timestamp in milliseconds
    etype: str  # Event type
    rtype: str  # Response event type
    args: NotRequired[list[Any]]  # Positional arguments
    kwargs: NotRequired[dict[str, Any]]  # Keyword arguments
    uuid: NotRequired[str]  # Request correlation ID


class RPCResponse(TypedDict, total=False):
    """
    RPC response where etype matches the request's rtype.

    Returns payload in data (server) or value (client).
    """
    ts: int  # Timestamp in milliseconds
    etype: str  # Matches request's rtype
    data: NotRequired[Any]  # Server response payload
    value: NotRequired[Any]  # Client response payload
    ok: NotRequired[bool]  # Success indicator
    error: NotRequired[Optional[str]]  # Error message if failed


class VuerComponent(TypedDict, total=False):
    """
    Vuer component schema.

    A (mostly) nested dictionary representing a scene graph node.
    All values can be primitives, ZData objects, or nested structures.
    """
    tag: str  # Component type (e.g., "mesh", "scene", "camera")
    children: NotRequired[list["VuerComponent"]]  # Nested components
    # Additional fields are dynamic and type-safe through TypedDict


# Type aliases for convenience
EventType = Union[Message, ClientEvent, ServerEvent, RPCRequest, RPCResponse]


def current_timestamp() -> int:
    """Get current timestamp in milliseconds."""
    return int(time.time() * 1000)


def create_client_event(
    etype: str,
    value: Any = None,
    key: Optional[str] = None,
    rtype: Optional[str] = None,
    ts: Optional[int] = None
) -> ClientEvent:
    """
    Create a client event.

    Args:
        etype: Event type identifier
        value: Client payload
        key: Optional entity identifier
        rtype: Optional response type for RPC
        ts: Optional timestamp (defaults to current time)

    Returns:
        ClientEvent dictionary
    """
    event: ClientEvent = {
        "ts": ts or current_timestamp(),
        "etype": etype,
    }
    if value is not None:
        event["value"] = value
    if key is not None:
        event["key"] = key
    if rtype is not None:
        event["rtype"] = rtype
    return event


def create_server_event(
    etype: str,
    data: Any,
    ts: Optional[int] = None
) -> ServerEvent:
    """
    Create a server event.

    Args:
        etype: Event type identifier
        data: Server payload
        ts: Optional timestamp (defaults to current time)

    Returns:
        ServerEvent dictionary
    """
    return {
        "ts": ts or current_timestamp(),
        "etype": etype,
        "data": data,
    }


def create_rpc_request(
    etype: str,
    rtype: str,
    args: Optional[list[Any]] = None,
    kwargs: Optional[dict[str, Any]] = None,
    uuid: Optional[str] = None,
    ts: Optional[int] = None
) -> RPCRequest:
    """
    Create an RPC request.

    Args:
        etype: Event type identifier
        rtype: Response event type
        args: Optional positional arguments
        kwargs: Optional keyword arguments
        uuid: Optional request correlation ID
        ts: Optional timestamp (defaults to current time)

    Returns:
        RPCRequest dictionary
    """
    request: RPCRequest = {
        "ts": ts or current_timestamp(),
        "etype": etype,
        "rtype": rtype,
    }
    if args is not None:
        request["args"] = args
    if kwargs is not None:
        request["kwargs"] = kwargs
    if uuid is not None:
        request["uuid"] = uuid
    return request


def create_rpc_response(
    etype: str,
    data: Any = None,
    value: Any = None,
    ok: bool = True,
    error: Optional[str] = None,
    ts: Optional[int] = None
) -> RPCResponse:
    """
    Create an RPC response.

    Args:
        etype: Event type (should match request's rtype)
        data: Optional server response payload
        value: Optional client response payload
        ok: Success indicator
        error: Error message if failed
        ts: Optional timestamp (defaults to current time)

    Returns:
        RPCResponse dictionary
    """
    response: RPCResponse = {
        "ts": ts or current_timestamp(),
        "etype": etype,
        "ok": ok,
        "error": error,
    }
    if data is not None:
        response["data"] = data
    if value is not None:
        response["value"] = value
    return response
