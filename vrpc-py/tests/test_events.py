"""
Tests for event factory functions.
"""

import pytest
from vuer_rpc import (
    set_event,
    add_event,
    update_event,
    upsert_event,
    remove_event,
    timeout_event,
)


def test_set_event():
    """Test SET event creation."""
    scene = {"tag": "scene", "key": "root", "bgColor": [0, 0, 0]}
    event = set_event(scene)

    assert event["etype"] == "SET"
    assert event["data"] == scene
    assert "ts" in event

    # With custom timestamp
    ts = 1234567890
    event_ts = set_event(scene, ts=ts)
    assert event_ts["ts"] == ts


def test_add_event():
    """Test ADD event creation."""
    nodes = [
        {"tag": "mesh", "key": "box1", "position": [0, 0, 0]},
        {"tag": "mesh", "key": "box2", "position": [1, 1, 1]},
    ]

    event = add_event(nodes)

    assert event["etype"] == "ADD"
    assert event["data"]["nodes"] == nodes
    assert event["data"]["to"] == "children"
    assert "ts" in event

    # With custom target
    event_custom = add_event(nodes, to="scene")
    assert event_custom["data"]["to"] == "scene"


def test_update_event():
    """Test UPDATE event creation."""
    updates = [
        {"key": "box1", "position": [1, 0, 0]},
        {"key": "box2", "rotation": [0, 45, 0]},
    ]

    event = update_event(updates)

    assert event["etype"] == "UPDATE"
    assert event["data"]["nodes"] == updates
    assert "ts" in event


def test_upsert_event():
    """Test UPSERT event creation."""
    nodes = [
        {"tag": "mesh", "key": "box1", "position": [0, 0, 0]},
    ]

    event = upsert_event(nodes)

    assert event["etype"] == "UPSERT"
    assert event["data"]["nodes"] == nodes
    assert event["data"]["to"] == "children"

    # With custom target
    event_custom = upsert_event(nodes, to="scene")
    assert event_custom["data"]["to"] == "scene"


def test_remove_event():
    """Test REMOVE event creation."""
    keys = ["box1", "box2", "box3"]
    event = remove_event(keys)

    assert event["etype"] == "REMOVE"
    assert event["data"]["keys"] == keys
    assert "ts" in event


def test_timeout_event():
    """Test TIMEOUT event creation."""
    event = timeout_event(1.5, "updateScene")

    assert event["etype"] == "TIMEOUT"
    assert event["data"]["timeout"] == 1.5
    assert event["data"]["fn"] == "updateScene"
    assert "ts" in event


def test_event_timestamps():
    """Test that all events generate timestamps correctly."""
    import time

    before = int(time.time() * 1000)

    events = [
        set_event({"tag": "scene"}),
        add_event([]),
        update_event([]),
        upsert_event([]),
        remove_event([]),
        timeout_event(1.0, "fn"),
    ]

    after = int(time.time() * 1000)

    for event in events:
        assert "ts" in event
        assert before <= event["ts"] <= after
