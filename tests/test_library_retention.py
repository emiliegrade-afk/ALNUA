"""Library retention policy tests."""

from __future__ import annotations

import json

import pytest

from services.library_retention import preview_retention, apply_retention


def test_preview_retention_empty(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    lib = tmp_path / "bureau_library.json"
    lib.write_text(
        '{"version":1,"entries":[],"reports":[],"archives":[]}',
        encoding="utf-8",
    )
    ledger = tmp_path / "library_distribution.json"
    ledger.write_text('{"version":1,"receipts":{},"jobs":{}}', encoding="utf-8")
    monkeypatch.setattr("services.bureau_library.LIBRARY_FILE", lib)
    monkeypatch.setattr("services.library_distribution.LEDGER_FILE", ledger)

    preview = preview_retention()
    assert preview["total_entries"] == 0
    assert preview["compress_candidates"] == 0


def test_purge_short_summary(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    lib = tmp_path / "bureau_library.json"
    lib.write_text(
        json.dumps(
            {
                "version": 1,
                "entries": [
                    {
                        "id": "e1",
                        "bureau": "hub",
                        "title": "Test",
                        "summary": "court",
                        "timing": "later",
                        "created_at": "2020-01-01T00:00:00+00:00",
                    }
                ],
                "reports": [],
                "archives": [],
            }
        ),
        encoding="utf-8",
    )
    ledger = tmp_path / "library_distribution.json"
    ledger.write_text('{"version":1,"receipts":{},"jobs":{}}', encoding="utf-8")
    policy = tmp_path / "library_retention_policy.json"
    policy.write_text("{}", encoding="utf-8")
    monkeypatch.setattr("services.bureau_library.LIBRARY_FILE", lib)
    monkeypatch.setattr("services.library_distribution.LEDGER_FILE", ledger)
    monkeypatch.setattr("services.library_retention.POLICY_FILE", policy)

    result = apply_retention(dry_run=False)
    assert result["purged"] == 1
    assert result["remaining_entries"] == 0
