"""Shared helpers for ALNUA Telegram bots."""

from __future__ import annotations

import atexit
import logging
import os
from collections.abc import Awaitable, Callable
from pathlib import Path

from telegram.ext import Application

logger = logging.getLogger(__name__)

TELEGRAM_CHUNK_SIZE = 4000


def split_message(text: str, chunk_size: int = TELEGRAM_CHUNK_SIZE) -> list[str]:
    if len(text) <= chunk_size:
        return [text]
    return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]


def pid_is_running(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        import ctypes

        handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
        if handle:
            ctypes.windll.kernel32.CloseHandle(handle)
            return True
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def acquire_single_instance_lock(lock_file: Path) -> None:
    if lock_file.exists():
        try:
            old_pid = int(lock_file.read_text().strip())
        except ValueError:
            lock_file.unlink(missing_ok=True)
        else:
            if pid_is_running(old_pid):
                raise RuntimeError(
                    f"Bot Telegram déjà actif (PID {old_pid}). "
                    "Arrête l'autre instance avant de relancer."
                )
            lock_file.unlink(missing_ok=True)

    lock_file.write_text(str(os.getpid()), encoding="utf-8")
    atexit.register(lambda: lock_file.unlink(missing_ok=True))


def presence_callbacks(
    *,
    token: str,
    chat_id: int | None,
    back_message: str,
    coffee_message: str,
) -> tuple[Callable[[Application], Awaitable[None]], Callable[[Application], Awaitable[None]]]:
    """Callbacks for Application.builder().post_init / post_shutdown."""

    async def _post_init(_app: Application) -> None:
        if chat_id is None:
            return
        from services.telegram_presence import notify_presence

        try:
            await notify_presence(token=token, chat_id=chat_id, message=back_message)
        except Exception as exc:
            logger.warning("presence back message failed: %s", exc)

    async def _post_shutdown(_app: Application) -> None:
        if chat_id is None:
            return
        from services.telegram_presence import notify_presence

        try:
            await notify_presence(token=token, chat_id=chat_id, message=coffee_message)
        except Exception as exc:
            logger.warning("presence coffee message failed: %s", exc)

    def _atexit_coffee() -> None:
        if chat_id is None:
            return
        from services.telegram_presence import send_telegram_text

        send_telegram_text(token, chat_id, coffee_message)

    atexit.register(_atexit_coffee)
    return _post_init, _post_shutdown
