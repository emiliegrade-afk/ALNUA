"""Studio prompt preview — shot index integration."""

from __future__ import annotations

from services.studio.prompts import _shot_prompt_block, build_studio_prompt_preview


def test_shot_prompt_block_includes_description() -> None:
    block = _shot_prompt_block(
        {"number": 2, "type": "B-roll", "description": "Plans mains clavier", "duration_sec": 8},
        1,
    )
    assert "Plan 2" in block
    assert "Plans mains clavier" in block
    assert "8s" in block


def test_build_preview_with_shot_index(monkeypatch) -> None:
    from database.supabase_client import SupabaseClient

    class _Db(SupabaseClient):
        pass

    db = _Db.__new__(_Db)

    def _fake_shot(idea_id, user_id, shot_index, db_arg):
        if shot_index == 0:
            return {"number": 1, "type": "A-roll", "description": "Accroche face cam", "duration_sec": 6}
        return None

    def _fake_scripts(idea_id, user_id, artifact_type, db_arg):
        return []

    monkeypatch.setattr("services.studio.prompts._shot_at_index", _fake_shot)
    monkeypatch.setattr("services.studio.prompts.list_idea_artifacts", _fake_scripts)
    monkeypatch.setattr(
        "services.studio.prompts.build_studio_prompt",
        lambda idea, user_id: "BASE",
    )
    monkeypatch.setattr(
        "services.studio.prompts.build_dna_context_block",
        lambda user_id, project_id: "",
    )

    idea = {"id": "idea-1", "title": "T", "content": "C", "platform_target": "youtube"}
    out = build_studio_prompt_preview(idea, "user-1", tool_id="veo3_video", shot_index=0, db=db)
    assert "Accroche face cam" in out["prompt"]
    assert out["default_params"]["duration"] == 5

    out_all = build_studio_prompt_preview(idea, "user-1", tool_id="veo3_video", shot_index=None, db=db)
    assert "Accroche face cam" not in out_all["prompt"]
