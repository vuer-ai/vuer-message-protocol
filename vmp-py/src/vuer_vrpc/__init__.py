"""
Vuer Message Protocol (VMP) - Python Implementation

A lightweight, cross-language messaging and RPC protocol designed for
use with Vuer and Zaku.

Main exports:
    - ZData: Extensible type encoding for numpy, torch, PIL, and custom types
    - Message types: Message, ClientEvent, ServerEvent, RPCRequest, RPCResponse
    - Event factories: set_event, add_event, update_event, upsert_event, remove_event
    - Serializers: MessagePackSerializer, JSONSerializer

Example:
    >>> import numpy as np
    >>> from vmp_py import ZData, MessagePackSerializer, set_event
    >>>
    >>> # Encode numpy array
    >>> arr = np.array([1, 2, 3])
    >>> encoded = ZData.encode(arr)
    >>>
    >>> # Create and serialize an event
    >>> event = set_event({"tag": "scene", "data": arr})
    >>> serializer = MessagePackSerializer()
    >>> binary = serializer.encode(event)
    >>>
    >>> # Decode
    >>> decoded_event = serializer.decode(binary)
"""

# ZData encoding
from .zdata import ZData
from .type_registry import TYPE_REGISTRY, TypeRegistry

# Message types
from .types import (
    Message,
    ClientEvent,
    ServerEvent,
    RPCRequest,
    RPCResponse,
    VuerComponent,
    EventType,
    current_timestamp,
    create_client_event,
    create_server_event,
    create_rpc_request,
    create_rpc_response,
)

# Event factories
from .events import (
    set_event,
    add_event,
    update_event,
    upsert_event,
    remove_event,
    timeout_event,
)

# Serializers
from .serializers import (
    MessagePackSerializer,
    JSONSerializer,
    msgpack_serializer,
    json_serializer,
)

__version__ = "0.1.0"

__all__ = [
    # ZData
    "ZData",
    "TYPE_REGISTRY",
    "TypeRegistry",
    # Types
    "Message",
    "ClientEvent",
    "ServerEvent",
    "RPCRequest",
    "RPCResponse",
    "VuerComponent",
    "EventType",
    "current_timestamp",
    "create_client_event",
    "create_server_event",
    "create_rpc_request",
    "create_rpc_response",
    # Events
    "set_event",
    "add_event",
    "update_event",
    "upsert_event",
    "remove_event",
    "timeout_event",
    # Serializers
    "MessagePackSerializer",
    "JSONSerializer",
    "msgpack_serializer",
    "json_serializer",
]
