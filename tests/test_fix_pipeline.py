"""Tests for fix_pipeline — deploy detection, context levels, reviews (mocked LLM)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch


from agents import fix_pipeline


class TestContextLevels:
    def test_levels_increase_with_attempts(self) -> None:
        assert fix_pipeline.CONTEXT_LEVELS[0]["files"] < fix_pipeline.CONTEXT_LEVELS[-1]["files"]
        assert fix_pipeline.CONTEXT_LEVELS[0]["depth"] == "shallow"
        assert fix_pipeline.CONTEXT_LEVELS[-1]["depth"] == "exhaustive"

    def test_max_attempts_positive(self) -> None:
        assert fix_pipeline.MAX_PIPELINE_ATTEMPTS >= 1


class TestDeployDetection:
    def test_detects_docker_compose(self, tmp_path: Path) -> None:
        (tmp_path / "docker-compose.yml").write_text("version: '3'\n")
        result = fix_pipeline._detect_deploy_method(str(tmp_path))
        assert result["method"] == "docker"

    def test_unknown_empty_repo(self, tmp_path: Path) -> None:
        result = fix_pipeline._detect_deploy_method(str(tmp_path))
        assert result["method"] == "unknown"


class TestQAReview:
    def test_qa_review_parses_json(self) -> None:
        with patch.object(fix_pipeline, "_llm", return_value='{"approved": true, "feedback": "OK"}'):
            result = fix_pipeline._qa_review("diff", "TypeError", "fixed null check")
        assert result["approved"] is True

    def test_qa_review_fails_safe_on_error(self) -> None:
        with patch.object(fix_pipeline, "_llm", side_effect=RuntimeError("API down")):
            result = fix_pipeline._qa_review("diff", "error", "fix")
        assert result["approved"] is False


class TestSpecReview:
    def test_spec_review_rejects_on_parse_failure(self) -> None:
        with patch.object(fix_pipeline, "_llm", return_value="not json"):
            result = fix_pipeline._spec_review("diff", "summary", "context")
        assert result["approved"] is False
