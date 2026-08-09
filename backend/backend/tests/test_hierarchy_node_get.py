import json
import pytest

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_get_existing_node_returns_200():
    res = client.get("/api/v1/hierarchy")
    assert res.status_code == 200
    tree = res.json()
    # find a chat node
    def find(n):
        if not n:
            return None
        if n.get("type") == "chat":
            return n
        for c in n.get("children", []):
            r = find(c)
            if r:
                return r
        return None

    chat = find(tree["root"]) if tree else None
    assert chat is not None

    node_id = chat["id"]

    res2 = client.get(f"/api/v1/hierarchy/{node_id}")
    assert res2.status_code == 200
    node = res2.json()
    assert node["id"] == node_id
    assert node["type"] == "chat"
    assert node.get("metadata") is not None
    assert node["metadata"].get("entity_type") == "conversation"
    assert isinstance(node["metadata"].get("entity_id"), str)


def test_get_unknown_node_returns_404():
    res = client.get("/api/v1/hierarchy/not-a-node")
    assert res.status_code == 404
