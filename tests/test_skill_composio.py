"""Tests skill_composio — nécessite COMPOSIO_API_KEY dans .env"""
import os
import pytest


def test_import():
    from skills.skill_composio import get_composio_tools, composio_execute, get_oauth_link
    assert callable(get_composio_tools)


def test_no_api_key(monkeypatch):
    monkeypatch.delenv("COMPOSIO_API_KEY", raising=False)
    from skills.skill_composio import get_composio_tools
    tools = get_composio_tools(apps=["GMAIL"])
    assert tools == []  # graceful fallback


@pytest.mark.skipif(not os.getenv("COMPOSIO_API_KEY"), reason="COMPOSIO_API_KEY required")
def test_get_tools_coo():
    from skills.skill_composio import get_composio_tools
    tools = get_composio_tools(agent_name="coo_agent", user_id="test_user")
    assert isinstance(tools, list)


@pytest.mark.skipif(not os.getenv("COMPOSIO_API_KEY"), reason="COMPOSIO_API_KEY required")
def test_list_connected_apps():
    from skills.skill_composio import list_connected_apps
    apps = list_connected_apps(user_id="test_user")
    assert isinstance(apps, list)
