"""
Event factory functions for Vuer scene graph operations.

Provides convenient functions for creating common event types
used in Vuer's scene graph manipulation.
"""

from typing import Any, Optional
from .types import ServerEvent, VuerComponent, current_timestamp


def set_event(
    scene: dict[str, Any],
    ts: Optional[int] = None
) -> ServerEvent:
    """
    Create a SET event to initialize or reset the scene.

    Args:
        scene: Scene configuration with at least a 'tag' field
        ts: Optional timestamp (defaults to current time)

    Returns:
        ServerEvent with etype "SET"

    Example:
        >>> set_event({"tag": "scene", "key": "root", "children": []})
        {'ts': 1234567890, 'etype': 'SET', 'data': {...}}
    """
    return {
        "ts": ts or current_timestamp(),
        "etype": "SET",
        "data": scene,
    }


def add_event(
    nodes: list[VuerComponent],
    to: str = "children",
    ts: Optional[int] = None
) -> ServerEvent:
    """
    Create an ADD event to add nodes to the scene.

    Args:
        nodes: List of nodes to add
        to: Target location (default: "children")
        ts: Optional timestamp (defaults to current time)

    Returns:
        ServerEvent with etype "ADD"

    Example:
        >>> add_event([{"tag": "mesh", "key": "box1"}], to="children")
        {'ts': 1234567890, 'etype': 'ADD', 'data': {'nodes': [...], 'to': 'children'}}
    """
    return {
        "ts": ts or current_timestamp(),
        "etype": "ADD",
        "data": {
            "nodes": nodes,
            "to": to,
        },
    }


def update_event(
    nodes: list[dict[str, Any]],
    ts: Optional[int] = None
) -> ServerEvent:
    """
    Create an UPDATE event to update existing nodes.

    Args:
        nodes: List of node updates (must include 'key' field)
        ts: Optional timestamp (defaults to current time)

    Returns:
        ServerEvent with etype "UPDATE"

    Example:
        >>> update_event([{"key": "box1", "position": [1, 2, 3]}])
        {'ts': 1234567890, 'etype': 'UPDATE', 'data': {'nodes': [...]}}
    """
    return {
        "ts": ts or current_timestamp(),
        "etype": "UPDATE",
        "data": {
            "nodes": nodes,
        },
    }


def upsert_event(
    nodes: list[VuerComponent],
    to: str = "children",
    ts: Optional[int] = None
) -> ServerEvent:
    """
    Create an UPSERT event to insert or update nodes (idempotent).

    Args:
        nodes: List of nodes to upsert
        to: Target location (default: "children")
        ts: Optional timestamp (defaults to current time)

    Returns:
        ServerEvent with etype "UPSERT"

    Example:
        >>> upsert_event([{"tag": "mesh", "key": "box1"}])
        {'ts': 1234567890, 'etype': 'UPSERT', 'data': {'nodes': [...], 'to': 'children'}}
    """
    return {
        "ts": ts or current_timestamp(),
        "etype": "UPSERT",
        "data": {
            "nodes": nodes,
            "to": to,
        },
    }


def remove_event(
    keys: list[str],
    ts: Optional[int] = None
) -> ServerEvent:
    """
    Create a REMOVE event to remove nodes from the scene.

    Args:
        keys: List of node keys to remove
        ts: Optional timestamp (defaults to current time)

    Returns:
        ServerEvent with etype "REMOVE"

    Example:
        >>> remove_event(["box1", "box2"])
        {'ts': 1234567890, 'etype': 'REMOVE', 'data': {'keys': ['box1', 'box2']}}
    """
    return {
        "ts": ts or current_timestamp(),
        "etype": "REMOVE",
        "data": {
            "keys": keys,
        },
    }


def timeout_event(
    timeout: float,
    fn: str,
    ts: Optional[int] = None
) -> ServerEvent:
    """
    Create a TIMEOUT event for scheduled execution.

    Args:
        timeout: Delay in seconds
        fn: Function identifier or code to execute
        ts: Optional timestamp (defaults to current time)

    Returns:
        ServerEvent with etype "TIMEOUT"

    Example:
        >>> timeout_event(1.5, "updateScene")
        {'ts': 1234567890, 'etype': 'TIMEOUT', 'data': {'timeout': 1.5, 'fn': 'updateScene'}}
    """
    return {
        "ts": ts or current_timestamp(),
        "etype": "TIMEOUT",
        "data": {
            "timeout": timeout,
            "fn": fn,
        },
    }
