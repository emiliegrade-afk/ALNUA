# ALNUA Test — Stratégie Tests & Playwright

Tests ALNUA Hub : pytest (backend) + Playwright (E2E frontend + API). Alex Okafor (QA) valide.

---

## Structure tests

```
tests/
  test_agents/
    test_analyst_business.py
    test_analyst_data.py
    test_secretary.py
    [...]
  test_services/
    test_competition.py
    test_llm_router.py
    test_adversarial_spec.py
    test_parallel_runner.py
    test_content_pipeline.py
  test_api/
    test_agents_pole.py
    test_advanced_services.py
  e2e/
    test_hub_pages.py   ← Playwright
```

---

## Pattern test agent (pytest)

```python
import pytest
from unittest.mock import patch, MagicMock
from agents.my_agent import MyAgent

@pytest.fixture
def agent():
    with patch("agents.my_agent.LLMClient") as mock_llm, \
         patch("agents.my_agent.get_supabase") as mock_db:
        mock_llm.return_value.complete.return_value = '{"result": "ok", "details": "..."}'
        mock_db.return_value.insert.return_value = {"id": "test-uuid"}
        yield MyAgent()

def test_my_method_basic(agent):
    result = agent.my_method("test input")
    assert "result" in result
    assert result["result"] == "ok"

def test_my_method_empty_input(agent):
    """Alex checke toujours les cas limites."""
    result = agent.my_method("")
    assert isinstance(result, dict)

def test_my_method_long_input(agent):
    long_input = "x" * 5000
    result = agent.my_method(long_input)
    assert isinstance(result, dict)
```

---

## Pattern test endpoint FastAPI

```python
import pytest
from fastapi.testclient import TestClient
from api.app import app
from unittest.mock import patch

client = TestClient(app)

def test_endpoint_success():
    with patch("agents.my_agent.MyAgent.my_method") as mock:
        mock.return_value = {"result": "ok"}
        resp = client.post("/agents/my-agent/my-method", json={"param": "test"})
    assert resp.status_code == 200
    assert resp.json()["result"]["result"] == "ok"

def test_endpoint_missing_field():
    resp = client.post("/agents/my-agent/my-method", json={})
    assert resp.status_code == 422  # Pydantic validation

def test_endpoint_auth_required():
    """Si middleware HUB_API_KEY actif."""
    resp = client.post("/agents/my-agent/my-method",
                       json={"param": "test"},
                       headers={"X-Hub-Api-Key": "wrong"})
    assert resp.status_code in (401, 403)
```

---

## Test service competition

```python
from services.competition import add_points, get_scores

def test_add_points_known_action(tmp_path, monkeypatch):
    monkeypatch.setattr("services.competition._SCORES_PATH", tmp_path / "scores.json")
    result = add_points("dev_app", "task_completed")
    assert result["points_added"] == 10
    assert result["new_total"] == 10

def test_milestone_unlocked(tmp_path, monkeypatch):
    monkeypatch.setattr("services.competition._SCORES_PATH", tmp_path / "scores.json")
    for _ in range(10):  # 10 × 10pts = 100pts → milestone
        result = add_points("dev_app", "task_completed")
    assert result["milestone_unlocked"] == "coffee_break_100"
```

---

## Test LLM Router

```python
from services.llm_router import complexity_score, route_to_model

def test_complexity_score_simple():
    assert complexity_score("Bonjour", "sql_query") <= 3

def test_complexity_score_complex():
    prompt = "Analyse le marché et compare les concurrents avec les opportunités " * 10
    assert complexity_score(prompt, "market_analysis") >= 7

def test_router_never_downgrades_below_static():
    # dev_app est standard — ne peut pas être routé vers fast
    model = route_to_model("dev_app", "ok", "simple_task")
    from config.agent_models import TIER_MODELS
    assert model != TIER_MODELS["fast"]
```

---

## Playwright E2E (skill_playwright.py déjà dans le stack)

```python
# tests/e2e/test_hub_pages.py
import pytest
from playwright.sync_api import Page, expect

BASE_URL = "http://localhost:3000"

def test_homepage_loads(page: Page):
    page.goto(BASE_URL)
    expect(page).to_have_title("ALNUA Hub")

def test_analytics_room_accessible(page: Page):
    page.goto(f"{BASE_URL}/analytics")
    expect(page.locator("[data-agent='analyst_business']")).to_be_visible()
    expect(page.locator("[data-agent='analyst_data']")).to_be_visible()

def test_leaderboard_loads(page: Page):
    page.goto(f"{BASE_URL}/competition")
    leaderboard = page.locator("[data-testid='leaderboard']")
    expect(leaderboard).to_be_visible()
    # Au moins 1 agent dans le leaderboard
    rows = leaderboard.locator("tr")
    expect(rows).to_have_count(lambda c: c >= 1)
```

---

## Commandes

```bash
# Tests unitaires
pytest tests/ -v

# Tests avec coverage
pytest tests/ --cov=agents --cov=services --cov-report=term-missing

# Tests spécifiques
pytest tests/test_services/test_competition.py -v
pytest tests/test_api/ -v

# E2E Playwright (nécessite le serveur + frontend actifs)
pytest tests/e2e/ --headed

# Test adversarial spec
pytest tests/test_services/test_adversarial_spec.py -v -s
```

---

## Règles QA Alex

1. Chaque méthode agent a au minimum : test cas nominal + cas limite (input vide/long)
2. Chaque endpoint : test 200 + test 422 (champ manquant)
3. `log_agent_action()` ne doit jamais faire crasher une méthode — tester avec DB mock
4. Le score compétition est testé avec `monkeypatch` sur `_SCORES_PATH` — jamais sur le vrai fichier
5. Les mocks LLM retournent toujours du JSON valide pour tester `parse_json_response()`
