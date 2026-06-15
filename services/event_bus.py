"""
services/event_bus.py — Bus d'événements inter-agents ALNUA.

Inspiré de agent-memory-stream. Pub/sub léger : un agent émet un événement,
d'autres agents réagissent automatiquement selon leurs abonnements.

Exemples de flux automatisés :
- spec_validated → PM crée le sprint → COO valide
- feature_shipped → Marketing génère le post → Content rédige le blog
- budget_alert → Controller notifie → Accounting ajuste

Usage:
    from services.event_bus import emit, subscribe, get_recent_events

    # Émettre un event
    emit("spec_validated", payload={"spec_id": "v2.3", "agent": "spec"}, source_agent="spec")

    # S'abonner (handlers s'enregistrent au démarrage)
    @subscribe("spec_validated")
    def on_spec_validated(event):
        # PM crée automatiquement les tasks
        ...

    # Lire les events récents
    events = get_recent_events(event_type="feature_shipped", limit=10)
"""
from __future__ import annotations

import json
import logging
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)

from config.agent_personas import persona_first_name

# ---------------------------------------------------------------------------
# Types d'événements ALNUA
# ---------------------------------------------------------------------------

_SPEC = persona_first_name("spec")
_QA = persona_first_name("qa")

EVENT_TYPES = {
    # Pipeline spec
    "spec_created":      f"{_SPEC} a créé une spec",
    "spec_validated":    f"{_QA} a validé la spec → PM peut planifier",
    "spec_rejected":     f"{_QA} a rejeté la spec → {_SPEC} doit réviser",

    # Pipeline développement
    "feature_shipped":   "Feature livrée → Marketing + Content notifiés",
    "bug_reported":      "Bug détecté → Dev assigné",
    "bug_fixed":         "Bug corrigé → QA notifié pour vérification",
    "pr_reviewed":       "PR reviewée → Merge possible",

    # Pipeline contenu
    "brief_created":     "Brief créé → Pipeline contenu déclenché",
    "content_published": "Contenu publié → Métriques à suivre",

    # Finance
    "budget_alert":      "Budget dépassé → Controller + Accounting alertés",
    "invoice_created":   "Facture créée → Jules pour validation",

    # Agents
    "task_completed":    "Tâche agent complétée",
    "task_failed":       "Tâche agent échouée → Retry ou escalade",
    "agent_leveled_up":  "Agent a atteint un milestone compétition",

    # Custom
    "custom":            "Événement personnalisé",
}


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class Event:
    event_type: str
    payload: dict[str, Any]
    source_agent: str = ""
    event_id: str = field(default_factory=lambda: f"evt_{int(time.time()*1000)}")
    ts: float = field(default_factory=time.time)
    handled_by: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "source_agent": self.source_agent,
            "payload": self.payload,
            "ts": self.ts,
            "handled_by": self.handled_by,
        }


# ---------------------------------------------------------------------------
# Registry handlers + store events
# ---------------------------------------------------------------------------

_handlers: dict[str, list[Callable]] = defaultdict(list)
_event_store: list[Event] = []  # en mémoire, max 500 events
_store_lock = threading.Lock()
_EVENT_LOG_PATH = Path(__file__).parent.parent / "data" / "event_log.json"

MAX_STORE_SIZE = 500


def _persist_event(event: Event) -> None:
    try:
        _EVENT_LOG_PATH.parent.mkdir(exist_ok=True)
        existing = []
        if _EVENT_LOG_PATH.exists():
            try:
                existing = json.loads(_EVENT_LOG_PATH.read_text())
            except Exception:
                pass
        existing.append(event.to_dict())
        # Garde 1000 events max sur disque
        existing = existing[-1000:]
        _EVENT_LOG_PATH.write_text(json.dumps(existing, indent=2))
    except Exception as e:
        logger.debug(f"event_bus persist failed: {e}")


def subscribe(event_type: str) -> Callable:
    """Décorateur : @subscribe('spec_validated') sur un handler."""
    def decorator(fn: Callable) -> Callable:
        _handlers[event_type].append(fn)
        logger.debug(f"event_bus: handler registered for '{event_type}': {fn.__name__}")
        return fn
    return decorator


def register_handler(event_type: str, handler: Callable) -> None:
    """Enregistre un handler programmatiquement (sans décorateur)."""
    _handlers[event_type].append(handler)


def emit(
    event_type: str,
    payload: dict[str, Any] | None = None,
    source_agent: str = "",
    async_handlers: bool = True,
) -> Event:
    """
    Émet un événement. Les handlers s'exécutent en arrière-plan (par défaut).

    Args:
        event_type:   Type d'event (voir EVENT_TYPES)
        payload:      Données de l'event
        source_agent: Agent émetteur
        async_handlers: True = handlers en threads daemon (non-bloquant)

    Returns:
        L'Event créé.
    """
    event = Event(
        event_type=event_type,
        payload=payload or {},
        source_agent=source_agent,
    )

    with _store_lock:
        _event_store.append(event)
        if len(_event_store) > MAX_STORE_SIZE:
            _event_store.pop(0)

    # Persister en background
    threading.Thread(target=_persist_event, args=(event,), daemon=True).start()

    # Déclencher les handlers
    handlers = _handlers.get(event_type, []) + _handlers.get("*", [])
    for handler in handlers:
        def run_handler(h: Callable, e: Event) -> None:
            try:
                h(e)
                e.handled_by.append(h.__name__)
                logger.info(f"event_bus: '{event_type}' handled by {h.__name__}")
            except Exception as ex:
                logger.warning(f"event_bus: handler {h.__name__} failed: {ex}")

        if async_handlers:
            threading.Thread(target=run_handler, args=(handler, event), daemon=True).start()
        else:
            run_handler(handler, event)

    logger.debug(f"event_bus: emitted '{event_type}' from {source_agent or 'unknown'} → {len(handlers)} handlers")
    return event


def get_recent_events(
    event_type: str | None = None,
    source_agent: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """
    Retourne les events récents du store en mémoire.
    Endpoint: GET /services/events/recent
    """
    with _store_lock:
        events = list(_event_store)

    if event_type:
        events = [e for e in events if e.event_type == event_type]
    if source_agent:
        events = [e for e in events if e.source_agent == source_agent]

    return [e.to_dict() for e in reversed(events[-limit:])]


def get_event_stats() -> dict[str, Any]:
    """
    Stats des events : counts par type, agents les plus actifs.
    Endpoint: GET /services/events/stats
    """
    with _store_lock:
        events = list(_event_store)

    type_counts: dict[str, int] = defaultdict(int)
    agent_counts: dict[str, int] = defaultdict(int)

    for e in events:
        type_counts[e.event_type] += 1
        if e.source_agent:
            agent_counts[e.source_agent] += 1

    return {
        "total_events_in_memory": len(events),
        "by_type": dict(sorted(type_counts.items(), key=lambda x: x[1], reverse=True)),
        "by_source_agent": dict(sorted(agent_counts.items(), key=lambda x: x[1], reverse=True)),
        "registered_handlers": {k: len(v) for k, v in _handlers.items()},
        "available_event_types": EVENT_TYPES,
    }


def clear_store() -> dict[str, str]:
    """Vide le store en mémoire (logs sur disque conservés)."""
    with _store_lock:
        count = len(_event_store)
        _event_store.clear()
    return {"cleared": str(count), "status": "ok"}


# ---------------------------------------------------------------------------
# Handlers ALNUA pré-câblés
# ---------------------------------------------------------------------------

@subscribe("feature_shipped")
def _on_feature_shipped(event: Event) -> None:
    """Quand une feature est livrée → pipeline contenu automatique."""
    try:
        feature = event.payload.get("feature", "nouvelle feature")
        from services.competition import add_points
        source = event.source_agent or "dev_app"
        add_points(source, "feature_shipped", note=f"Event: {feature[:40]}")
    except Exception:
        pass


@subscribe("budget_alert")
def _on_budget_alert(event: Event) -> None:
    """Quand le budget est dépassé → log pour Rémi (controller)."""
    severity = event.payload.get("severity", "warning")
    spent = event.payload.get("spent_usd", 0)
    logger.warning(f"BUDGET ALERT [{severity}]: ${spent} spent today")


@subscribe("task_failed")
def _on_task_failed(event: Event) -> None:
    """Log des échecs pour monitoring."""
    agent = event.payload.get("agent_id", "unknown")
    error = event.payload.get("error", "")
    logger.error(f"task_failed event: agent={agent} error={error[:100]}")
