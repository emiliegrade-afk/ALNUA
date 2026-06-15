"""Tests for services/coding_pipeline.py — Super Plan Phase 1."""

from __future__ import annotations

from services.coding_pipeline import DevStack, detect_stack, get_coding_config


def test_coding_config_defaults() -> None:
    cfg = get_coding_config()
    assert cfg.timeout_s >= 600
    assert cfg.max_turns >= 10
    assert cfg.max_parallel >= 1


def test_detect_stack_expo_from_description() -> None:
    stack = detect_stack(
        {
            "description": "Build Expo app with Mapbox and Supabase auth",
            "files_to_create": ["app/(tabs)/map.tsx"],
        }
    )
    assert stack == DevStack.REACT_NATIVE_EXPO


def test_detect_stack_explicit() -> None:
    stack = detect_stack({"stack": "nextjs", "description": "anything"})
    assert stack == DevStack.NEXTJS


def test_detect_stack_hub_default() -> None:
    stack = detect_stack(
        {
            "description": "Add feature",
            "repo_slug": "hub",
        }
    )
    assert stack == DevStack.PYTHON_FASTAPI


def test_detect_stack_academy_default() -> None:
    stack = detect_stack({"description": "Exercise", "repo_slug": "academy"})
    assert stack == DevStack.REACT_NATIVE_EXPO
