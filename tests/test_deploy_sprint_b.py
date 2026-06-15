"""Sprint B — deploy scripts, n8n vars, CORS prod."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.parametrize(
    "relative",
    [
        "scripts/verify_deploy.py",
        "scripts/activate_prod_flags.py",
        "deploy/SPRINT_B.md",
    ],
)
def test_sprint_b_artifacts_exist(relative: str) -> None:
    assert (ROOT / relative).is_file(), f"missing {relative}"


@pytest.mark.parametrize("workflow", ["01-morning-briefing", "02-github-pr-review", "03-spec-qa-chain", "04-welcome-user", "05-content-sprint"])
def test_n8n_workflows_use_hub_vars(workflow: str) -> None:
    path = ROOT / "n8n" / "workflows" / f"{workflow}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    blob = json.dumps(data)
    assert "$vars.HUB_API_URL" in blob, f"{workflow} missing HUB_API_URL var"
    assert "$vars.HUB_API_KEY" in blob, f"{workflow} missing HUB_API_KEY var"
    assert "localhost:8000" not in blob, f"{workflow} still hardcodes localhost"
    assert "alnua_dev_" not in blob, f"{workflow} still hardcodes dev key"


def test_nginx_uses_api_alnua_domain() -> None:
    text = (ROOT / "deploy" / "nginx.conf").read_text(encoding="utf-8")
    assert "api.alnua.com" in text
    assert "ton-domaine.fr" not in text


def test_api_cors_includes_portal_from_settings() -> None:
    text = (ROOT / "api" / "app.py").read_text(encoding="utf-8")
    assert "_cors_origins" in text
    assert "beta_portal_base_url" in text
    assert "VERCEL_URL" in text


def test_root_package_json_deploy_scripts() -> None:
    text = (ROOT / "package.json").read_text(encoding="utf-8")
    assert "deploy:verify" in text
    assert "deploy:build-web" in text
    assert "deploy:activate-prod-flags" in text
