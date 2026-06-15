"""Phase 5 — DevOps artifacts smoke tests."""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


@pytest.mark.parametrize(
    "relative",
    [
        "docker-compose.dev.yml",
        "docker-compose.yml",
        "deploy/DEPLOY.md",
        "deploy/deploy.sh",
        "deploy/vercel.env.example",
        "deploy/.env.prod.example",
        "web/vercel.json",
        "scripts/dev.ps1",
        "scripts/dev_ports.ps1",
        "pytest.ini",
        "Dockerfile.dev",
        "requirements-dev.txt",
    ],
)
def test_phase5_devops_files_exist(relative: str) -> None:
    assert (ROOT / relative).is_file(), f"missing {relative}"


def test_docker_compose_dev_declares_hub_api() -> None:
    text = (ROOT / "docker-compose.dev.yml").read_text(encoding="utf-8")
    assert "hub_api:" in text
    assert "--reload" in text
    assert "8000:8000" in text


def test_docker_compose_prod_persists_data() -> None:
    text = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    assert "./data:/app/data" in text


def test_root_package_json_dev_scripts() -> None:
    text = (ROOT / "package.json").read_text(encoding="utf-8")
    assert "dev:api" in text
    assert "dev:web" in text
    assert "dev:docker" in text
    assert "dev:status" in text
    assert "dev:stop" in text


def test_docker_compose_dev_uses_lightweight_dockerfile() -> None:
    text = (ROOT / "docker-compose.dev.yml").read_text(encoding="utf-8")
    assert "Dockerfile.dev" in text


def test_env_prod_example_has_phase_flags() -> None:
    text = (ROOT / "deploy" / ".env.prod.example").read_text(encoding="utf-8")
    assert "ADMIN_COSTS_PAGE_ENABLED" in text
    assert "GDD_MANAGER_ENABLED" in text
    assert "HUB_API_URL" in text
