"""CreatorFlow — BYOK secret envelope (Fernet v2, XOR v1 legacy)."""

from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from config.settings import get_settings

_FERNET_PREFIX = "v2:"


def _derive_key(user_id: str) -> bytes:
    settings = get_settings()
    secret = (settings.jwt_secret or settings.hub_api_key or "cf-dev-secret").strip()
    return hashlib.sha256(f"cf-byok:{secret}:{user_id}".encode()).digest()


def _fernet_for_user(user_id: str) -> Fernet:
    # Fernet expects 32 url-safe base64-encoded bytes.
    return Fernet(base64.urlsafe_b64encode(_derive_key(user_id)))


def encrypt_user_secret(user_id: str, plaintext: str) -> str:
    token = _fernet_for_user(user_id).encrypt(plaintext.encode("utf-8"))
    return f"{_FERNET_PREFIX}{token.decode('ascii')}"


def decrypt_user_secret(user_id: str, encrypted: str) -> str:
    if encrypted.startswith(_FERNET_PREFIX):
        try:
            raw = _fernet_for_user(user_id).decrypt(
                encrypted[len(_FERNET_PREFIX) :].encode("ascii")
            )
            return raw.decode("utf-8")
        except InvalidToken as exc:
            raise ValueError("Invalid BYOK ciphertext") from exc

    # Legacy XOR envelope (pre-Phase 6) — still readable for existing rows.
    key = _derive_key(user_id)
    xored = base64.urlsafe_b64decode(encrypted.encode("ascii"))
    raw = bytes(b ^ key[i % len(key)] for i, b in enumerate(xored))
    return raw.decode("utf-8")


def mask_api_key(key: str) -> str:
    if len(key) <= 8:
        return "••••"
    return f"{key[:4]}…{key[-4:]}"
