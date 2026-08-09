"""Regression test for api/routers/tickets.py::update_ticket_status.

Before the fix, PATCHing the status of a nonexistent ticket silently
succeeded (or 500'd) instead of returning 404 — the same guard
`update_ticket` already has just above it in the same file.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from tests.conftest import HUB_HEADERS, FakeDB

# Tickets router binds `get_supabase` via star-import — patch the name where
# the handler looks it up (not only database.supabase_client.get_supabase).


def test_update_ticket_status_404_when_ticket_missing(
    hub_client: TestClient, monkeypatch
) -> None:
    monkeypatch.setattr("api.routers.tickets.get_supabase", lambda: FakeDB())
    res = hub_client.patch(
        "/tickets/does-not-exist/status",
        params={"status": "in_progress"},
        headers=HUB_HEADERS,
    )
    assert res.status_code == 404


def test_update_ticket_status_rejects_unknown_status(
    hub_client: TestClient, monkeypatch
) -> None:
    monkeypatch.setattr("api.routers.tickets.get_supabase", lambda: FakeDB())
    res = hub_client.patch(
        "/tickets/does-not-exist/status",
        params={"status": "bogus"},
        headers=HUB_HEADERS,
    )
    assert res.status_code == 400


def test_update_ticket_accepts_in_review_via_general_endpoint(
    hub_client: TestClient, monkeypatch
) -> None:
    """The frontend's `lib/tickets.ts::updateTicket()` PATCHes /tickets/{id}
    (the general endpoint), not /tickets/{id}/status — its Pydantic
    TicketUpdate.status pattern is a separate validation point that also
    needed the in_review value added (api/schemas.py)."""

    class FoundDB(FakeDB):
        def select(self, *args, **kwargs):
            return [{"id": "t1", "status": "open"}]

    monkeypatch.setattr("api.routers.tickets.get_supabase", lambda: FoundDB())
    res = hub_client.patch(
        "/tickets/t1",
        json={"status": "in_review"},
        headers=HUB_HEADERS,
    )
    assert res.status_code == 200


def test_update_ticket_status_accepts_in_review(hub_client: TestClient, monkeypatch) -> None:
    class FoundDB(FakeDB):
        def select(self, *args, **kwargs):
            return [{"id": "t1", "status": "open"}]

    monkeypatch.setattr("api.routers.tickets.get_supabase", lambda: FoundDB())
    res = hub_client.patch(
        "/tickets/t1/status",
        params={"status": "in_review"},
        headers=HUB_HEADERS,
    )
    assert res.status_code == 200
