"""Pydantic request/response models for the Hub API — façade."""

from __future__ import annotations

from fastapi import Header, HTTPException

from services.beta_portal import decode_tester_token

from api.schemas_agents_core import *  # noqa: F403
from api.schemas_agents_pole import *  # noqa: F403
from api.schemas_hub import *  # noqa: F403
from api.schemas_finance import *  # noqa: F403
from api.schemas_beta import *  # noqa: F403
from api.schemas_advanced import *  # noqa: F403

def beta_tester_auth(authorization: str | None = Header(default=None)) -> dict[str, str]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token requis")
    token = authorization.removeprefix("Bearer ").strip()
    return decode_tester_token(token)

