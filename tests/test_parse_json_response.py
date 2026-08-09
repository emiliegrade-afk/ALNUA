"""parse_json_response resilience — fences + trailing prose."""

from __future__ import annotations

import pytest

from agents.base import parse_json_response


def test_parse_json_plain_object() -> None:
    assert parse_json_response('{"a": 1}') == {"a": 1}


def test_parse_json_markdown_fence() -> None:
    raw = '```json\n{"synthese": "ok"}\n```'
    assert parse_json_response(raw)["synthese"] == "ok"


def test_parse_json_extra_trailing_prose() -> None:
    raw = '{\n  "synthese": "ok",\n  "alertes": []\n}\n\nVoici mon analyse en plus.'
    result = parse_json_response(raw)
    assert result["synthese"] == "ok"
    assert result["alertes"] == []


def test_parse_json_rejects_array() -> None:
    with pytest.raises(ValueError, match="JSON object"):
        parse_json_response("[1, 2]")
