"""Find free calendar windows in Europe/Paris working hours (DEC-038 two-step)."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from services.live_cards_format import list_card

_PARIS = ZoneInfo("Europe/Paris")
WORK_START = 9
WORK_END = 18
SLOT_MINUTES = 30


def free_slots_brief(*, days: int = 2, duration_minutes: int = 30) -> str:
    from services.secretary_composio import fetch_calendar_events, is_connected

    if not is_connected("googlecalendar"):
        return (
            "Google Calendar n'est pas connecté.\n"
            "Dis « connecte mon calendrier » puis redemande les créneaux."
        )
    span = max(1, min(days, 5))
    length = max(15, min(duration_minutes, 180))
    events = fetch_calendar_events(days_ahead=span)
    busy = [_parse_when(ev.get("when")) for ev in events]
    busy = [b for b in busy if b is not None]
    slots = _scan(span, length, busy)
    if not slots:
        return list_card(
            "Aucun créneau libre",
            [f"Rien de {length} min sur {span} jour(s) ouvrés (9h–18h)."],
        )
    return list_card(
        f"Créneaux libres ({length} min)",
        slots,
        lead="Rien n'est réservé — dis « planifie … » + date/heure pour poser un événement.",
    )


def _scan(days: int, length: int, busy: list[datetime]) -> list[str]:
    now = datetime.now(_PARIS).replace(second=0, microsecond=0)
    found: list[str] = []
    day = now.date()
    stepped = 0
    while stepped < days and len(found) < 8:
        if day.weekday() < 5:
            start = datetime(day.year, day.month, day.day, WORK_START, 0, tzinfo=_PARIS)
            end = datetime(day.year, day.month, day.day, WORK_END, 0, tzinfo=_PARIS)
            cursor = max(start, _ceil_slot(now if day == now.date() else start))
            while cursor + timedelta(minutes=length) <= end:
                window_end = cursor + timedelta(minutes=length)
                if not _overlaps(cursor, window_end, busy):
                    found.append(cursor.strftime("%a %d/%m %H:%M").replace(".", ""))
                cursor += timedelta(minutes=SLOT_MINUTES)
        day += timedelta(days=1)
        stepped += 1
    return found


def _ceil_slot(moment: datetime) -> datetime:
    extra = (SLOT_MINUTES - moment.minute % SLOT_MINUTES) % SLOT_MINUTES
    return (moment + timedelta(minutes=extra)).replace(second=0, microsecond=0)


def _overlaps(start: datetime, end: datetime, busy: list[datetime]) -> bool:
    block = timedelta(minutes=SLOT_MINUTES)
    for when in busy:
        other_end = when + block
        if start < other_end and end > when:
            return True
    return False


def _parse_when(raw: Any) -> datetime | None:
    text = str(raw or "").strip()
    if not text or text == "?":
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=_PARIS)
    return parsed.astimezone(_PARIS)
