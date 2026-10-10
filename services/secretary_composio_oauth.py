"""Composio OAuth and connection status for Nadia."""

from __future__ import annotations

import os
import re
from typing import Any

from config.settings import get_settings


def composio_user_id() -> str:
    """Shared OAuth identity for CEO tools (Gmail, Calendar)."""
    settings = get_settings()
    return (
        settings.composio_user_id.strip()
        or os.getenv("COMPOSIO_USER_ID", "").strip()
        or os.getenv("COMPOSIO_CEO_USER_ID", "").strip()
        or "alnua_coo"
    )


_OAUTH_HTTP = re.compile(r"https?://[^\s)\]>'\"<>]+")


def extract_oauth_url(text: str) -> str | None:
    """Pull the first http(s) URL out of a Telegram-style OAuth reply."""
    match = _OAUTH_HTTP.search(text or "")
    if not match:
        return None
    return match.group(0).rstrip(".,;\"'")


def split_oauth_reply(raw: str) -> tuple[str, str]:
    """Return (url, hint). JSON endpoints need a pure URL; Telegram keeps the prose."""
    text = (raw or "").strip()
    url = extract_oauth_url(text)
    if not url:
        return "", text
    hint = text.replace(url, " ").replace("🔗", "").strip()
    return url, hint


def expected_ceo_gmail() -> str:
    """Gmail account Emilie wants Nadia to use (default: alnua.global@gmail.com)."""
    return get_settings().ceo_gmail.strip().lower()


def connected_gmail_email() -> str | None:
    from skills.skill_composio import get_gmail_profile_email

    email = get_gmail_profile_email(composio_user_id())
    return email.lower() if email else None


def gmail_account_ok() -> bool:
    expected = expected_ceo_gmail()
    if not expected:
        return is_connected("gmail")
    current = connected_gmail_email()
    return bool(current and current == expected)


def _gmail_connect_instructions() -> str:
    expected = expected_ceo_gmail()
    if expected:
        return f"Connecte-toi avec **{expected}** (compte ALNUA)."
    return "Ouvre le lien et autorise l'accès Google."


_INSTAGRAM_TOOLKITS = ("instagram", "instagram_business")
_INSTAGRAM_HINT = (
    "Compte Instagram Professionnel lié à une Page Facebook "
    "(Meta refuse un compte perso via cette API)."
)


def get_oauth_link_for_ceo(app: str, *, force_reconnect: bool = False) -> str:
    from skills.skill_composio import disconnect_toolkit, get_oauth_link

    toolkit = app.upper()
    uid = composio_user_id()

    if toolkit in {"INSTAGRAM", "INSTAGRAM_BUSINESS"}:
        return _instagram_oauth(uid)

    if toolkit == "GMAIL" and force_reconnect:
        disconnect_toolkit(uid, "gmail")

    link = get_oauth_link(app=toolkit, user_id=uid)

    if link.startswith("Erreur") or "déjà connecté" in link.lower() or "deja connecte" in link.lower():
        if toolkit == "GMAIL" and is_connected("gmail"):
            current = connected_gmail_email()
            expected = expected_ceo_gmail()
            if expected and current and current != expected:
                disconnect_toolkit(uid, "gmail")
                link = get_oauth_link(app=toolkit, user_id=uid)
                if link.startswith("http"):
                    return (
                        f"⚠️ Gmail actuel : {current}\n"
                        f"Compte attendu : {expected}\n\n"
                        f"🔗 Reconnexion — {_gmail_connect_instructions()}\n{link}"
                    )
        return link

    if toolkit == "GMAIL" and link.startswith("http"):
        return f"🔗 {_gmail_connect_instructions()}\n{link}"

    return link


def _instagram_oauth(uid: str) -> str:
    from skills.skill_composio import get_oauth_link

    last = ""
    for slug in _INSTAGRAM_TOOLKITS:
        link = get_oauth_link(app=slug, user_id=uid)
        last = link
        lower = link.lower()
        if link.startswith("http"):
            return f"🔗 {_INSTAGRAM_HINT}\n{link}"
        if "déjà connecté" in lower or "deja connecte" in lower:
            return link
    return last or f"Erreur: {_INSTAGRAM_HINT}"


def list_ceo_connections() -> list[dict[str, Any]]:
    from skills.skill_composio import list_connected_apps

    return list_connected_apps(user_id=composio_user_id())


def is_connected(toolkit: str) -> bool:
    from skills.skill_composio import has_active_connection

    slug = toolkit.lower()
    uid = composio_user_id()
    if slug in _INSTAGRAM_TOOLKITS:
        return any(has_active_connection(uid, name) for name in _INSTAGRAM_TOOLKITS)
    return has_active_connection(uid, slug)


def connection_status_text() -> str:
    apps = list_ceo_connections()
    expected = expected_ceo_gmail()
    gmail_email = connected_gmail_email()

    if not apps:
        hint = f"\nCompte Gmail à utiliser : {expected}" if expected else ""
        return (
            "Aucune app connectée.\n"
            "• Telegram : `/connect gmail` puis `/connect calendar`"
            f"{hint}"
        )
    lines = ["Apps connectées :"]
    for row in apps:
        app = row.get("app", "?")
        extra = ""
        if app == "GMAIL" and gmail_email:
            extra = f" ({gmail_email})"
            if expected and gmail_email != expected:
                extra += " ⚠️ mauvais compte — `/connect gmail` pour reconnecter"
        lines.append(f"• {app}{extra} — {row.get('status', '?')}")
    if not is_connected("gmail"):
        lines.append(f"\n⚠️ Gmail non connecté — `/connect gmail` ({expected or 'Google'})")
    elif expected and gmail_email and gmail_email != expected:
        lines.append(f"\n⚠️ Attendu : {expected} — envoie `/connect gmail` pour changer.")
    if not is_connected("googlecalendar"):
        lines.append("⚠️ Calendar non connecté — `/connect calendar`")
    if not is_connected("discord"):
        lines.append("⚠️ Discord non connecté — `/connect discord`")
    if not is_connected("instagram"):
        lines.append("⚠️ Instagram non connecté — `/connect instagram`")
    return "\n".join(lines)
