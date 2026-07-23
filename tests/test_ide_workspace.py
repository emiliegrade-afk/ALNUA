"""Tests for IDE workspace path safety."""


import pytest

from services import ide_workspace as iw


def test_sandbox_created(tmp_path, monkeypatch):
    monkeypatch.setattr(iw, "_SANDBOX", tmp_path / "sandbox")
    root = iw._ensure_sandbox()
    assert root.is_dir()
    assert (root / "README.md").is_file()


def test_resolve_sandbox(monkeypatch, tmp_path):
    sb = tmp_path / "sb"
    sb.mkdir()
    monkeypatch.setattr(iw, "_ensure_sandbox", lambda: sb.resolve())
    path, ro = iw.resolve_workspace("sandbox")
    assert path == sb.resolve()
    assert ro is False


def test_safe_path_blocks_traversal(tmp_path, monkeypatch):
    monkeypatch.setattr(iw, "_hub_root", lambda: tmp_path.resolve())
    root = tmp_path
    (root / "ok.py").write_text("x", encoding="utf-8")
    with pytest.raises(ValueError):
        iw._safe_rel(root, "../outside")
