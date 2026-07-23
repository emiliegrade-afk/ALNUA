"""Library distribution ledger tests."""

from __future__ import annotations

import json

import pytest

from services.library_distribution import (
    get_distribution_status,
    is_distributed,
    record_distributed,
    receipt_key,
)


def test_receipt_key_format() -> None:
    assert receipt_key("abc", "dev_app") == "abc:dev_app"


def test_record_and_check_distributed(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    ledger = tmp_path / "library_distribution.json"
    ledger.write_text('{"version":1,"receipts":{},"jobs":{}}', encoding="utf-8")
    monkeypatch.setattr("services.library_distribution.LEDGER_FILE", ledger)

    record_distributed("entry-1", "coo")
    assert is_distributed("entry-1", "coo")
    assert not is_distributed("entry-1", "qa")


def test_distribution_status_counts(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    lib = tmp_path / "bureau_library.json"
    lib.write_text(
        json.dumps(
            {
                "version": 1,
                "entries": [
                    {
                        "id": "e1",
                        "bureau": "app",
                        "title": "Test",
                        "summary": "S",
                        "timing": "now",
                        "created_at": "2026-01-01T00:00:00+00:00",
                    }
                ],
                "reports": [],
            }
        ),
        encoding="utf-8",
    )
    ledger = tmp_path / "library_distribution.json"
    ledger.write_text(
        json.dumps(
            {
                "version": 1,
                "receipts": {
                    "e1:dev_app": {
                        "entry_id": "e1",
                        "agent_id": "dev_app",
                        "distributed_at": "2026-01-02T00:00:00+00:00",
                    }
                },
                "jobs": {},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr("services.bureau_library.LIBRARY_FILE", lib)
    monkeypatch.setattr("services.library_distribution.LEDGER_FILE", ledger)

    status = get_distribution_status()
    assert status["total_entries"] == 1
    assert status["total_slots"] == 2
    assert status["distributed_slots"] == 1
    assert status["entries_pending_distribution"] == 1
