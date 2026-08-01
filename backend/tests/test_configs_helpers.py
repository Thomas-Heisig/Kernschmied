from __future__ import annotations

from app.api.v1 import configs
from app.api.v1.configs_schema import ConfigUpdateRequest


def test_normalize_config_number():
    assert configs.normalize_config_number(1) == 1.0
    assert configs.normalize_config_number(1.5) == 1.5
    assert configs.normalize_config_number(True) is None
    assert configs.normalize_config_number(float("inf")) is None


def test_is_config_string_list():
    assert configs.is_config_string_list(["a", "b"]) is True
    assert configs.is_config_string_list([1, "a"]) is False
    assert configs.is_config_string_list("notlist") is False


def test_normalize_config_value_basic():
    assert configs.normalize_config_value(None) is None
    assert configs.normalize_config_value(True) is True
    assert configs.normalize_config_value(2) == 2
    assert configs.normalize_config_value(2.5) == 2.5
    assert configs.normalize_config_value("s") == "s"
    m = {"a": 1, "b": {"c": 2}}
    res = configs.normalize_config_value(m)
    assert res["a"] == 1
    assert res["b"]["c"] == 2


def test_build_config_set_kwargs_signatures():
    payload = ConfigUpdateRequest(value="x", expected_revision=5, reason="r")

    def s1(group, key, value, expected_revision=None, actor_id=None, request_id=None, reason=None):
        pass

    def s2(group, key, value):
        pass

    def s3(group, key, value, **kwargs):
        pass

    k1 = configs.build_config_set_kwargs(setter=s1, payload=payload, actor_id="a", request_id="r")
    assert k1 == {
        "expected_revision": 5,
        "actor_id": "a",
        "request_id": "r",
        "reason": "r",
    }

    k2 = configs.build_config_set_kwargs(setter=s2, payload=payload, actor_id="a", request_id="r")
    assert k2 == {}

    k3 = configs.build_config_set_kwargs(setter=s3, payload=payload, actor_id=None, request_id=None)
    assert k3 == {
        "expected_revision": 5,
        "actor_id": None,
        "request_id": None,
        "reason": "r",
    }


def test_add_normalized_entry_and_identifier_helpers():
    target = {}
    configs.add_normalized_entry(target=target, group=" G ", key=" K ", value=1)
    assert ("g", "k") in target
    assert target[("g", "k")] == 1

    assert configs.normalize_optional_identifier(None) is None
    assert configs.normalize_optional_identifier("  X ") == "X"
