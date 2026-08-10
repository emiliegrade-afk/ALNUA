"""Advanced services — Event Bus (peeled from advanced_services.py)."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter(prefix="/services", tags=["advanced-services"])


class EmitEventRequest(BaseModel):
    event_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    source_agent: str = ""


@router.post("/events/emit")
def events_emit(body: EmitEventRequest) -> dict[str, Any]:
    """Émet un événement sur le bus — déclenche les handlers abonnés."""
    from services.event_bus import emit
    event = emit(body.event_type, body.payload, body.source_agent)
    return event.to_dict()


@router.get("/events/recent")
def events_recent(
    event_type: str | None = None,
    source_agent: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Events récents du bus (en mémoire)."""
    from services.event_bus import get_recent_events
    return get_recent_events(event_type=event_type, source_agent=source_agent, limit=limit)


@router.get("/events/stats")
def events_stats() -> dict[str, Any]:
    """Stats du bus : counts par type, agents les plus actifs, handlers enregistrés."""
    from services.event_bus import get_event_stats
    return get_event_stats()


@router.get("/events/types")
def events_types() -> dict[str, str]:
    """Liste tous les types d'événements ALNUA disponibles."""
    from services.event_bus import EVENT_TYPES
    return EVENT_TYPES


@router.post("/events/clear")
def events_clear() -> dict[str, str]:
    """Vide le store en mémoire (logs disque conservés)."""
    from services.event_bus import clear_store
    return clear_store()
