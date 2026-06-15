"""Shared Runway Act-Two state presets for ALNUA agent portrait animations."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ActTwoState:
    name: str
    motion_brief: str
    expression_intensity: int
    body_control: bool
    recorder_title: str
    recorder_hint: str
    duration_seconds: float = 6.0


STATES: dict[str, ActTwoState] = {
    "idle": ActTwoState(
        name="idle",
        motion_brief="""
Subtle executive idle loop — zero background movement, only the character lives:
- Breathing cycle: chest rises gently every 3 seconds
- Eye blinks at 2s and 5s
- Very slight ambient hair movement (light air current)
- Micro head tilt 1–2 degrees, slow and imperceptible
- Eyes: slow scan left at 4s, return forward
- Soft subsurface skin light variation with breathing
- Background frozen — no camera drift, no office motion
""".strip(),
        expression_intensity=2,
        body_control=True,
        recorder_title="ALNUA Idle Reference Recorder",
        recorder_hint="Subtle motion only — background frozen",
    ),
    "working": ActTwoState(
        name="working",
        motion_brief="""
Focused working state loop — zero background movement, only the character lives:
- Forward lean of 3–4 degrees, focused posture
- Eyes scanning left-right as if reading screens, deliberate rhythm
- Fingers visible at frame bottom — subtle typing movement
- Occasional micro-frown of concentration
- Faster breathing than idle
- At 3 seconds: pause and think (stillness), then resume
- Background frozen — no camera drift, no office motion
""".strip(),
        expression_intensity=3,
        body_control=True,
        recorder_title="ALNUA Working Reference Recorder",
        recorder_hint="Lean forward, type, scan screens — background frozen",
    ),
    "alert": ActTwoState(
        name="alert",
        motion_brief="""
Error/alert state loop — zero background movement, only the character lives:
- Slight backward lean, tension in posture
- Eyebrows draw together, jaw tightens subtly
- Hand moves slowly to temple or chin at 2 seconds
- Eyes narrow, scanning something wrong off-screen
- Breathing slightly held
- Subtle red-tinted ambient light shift on face
- Returns to start position — seamless loop
- Background frozen — no camera drift, no office motion
""".strip(),
        expression_intensity=4,
        body_control=True,
        recorder_title="ALNUA Alert Reference Recorder",
        recorder_hint="Lean back, tension, hand to temple — background frozen",
        duration_seconds=5.0,
    ),
}

RECORD_CUES: dict[str, list[tuple[float, str]]] = {
    "idle": [
        (0.0, "Hold still — composed gaze forward"),
        (1.5, "Begin slow inhale (chest rises)"),
        (2.0, "BLINK"),
        (3.0, "Exhale — chest settles"),
        (4.0, "Slow eye scan LEFT → return center"),
        (5.0, "BLINK"),
        (6.0, "Hold — loop end"),
    ],
    "working": [
        (0.0, "Lean forward 3–4° — focused posture"),
        (0.5, "Eyes scan LEFT (screen 1)"),
        (1.2, "Eyes scan RIGHT (screen 2)"),
        (1.8, "Fingers typing — subtle, continuous"),
        (2.4, "Micro-frown — concentration"),
        (3.0, "PAUSE — think (freeze 0.5s)"),
        (3.6, "Resume typing + faster breathing"),
        (4.2, "Eyes scan LEFT → RIGHT"),
        (5.0, "Micro-frown, keep typing"),
        (6.0, "Loop end — hold focused lean"),
    ],
    "alert": [
        (0.0, "Composed — tension building"),
        (0.8, "Slight backward lean — eyebrows knit"),
        (1.5, "Eyes narrow — scan off-screen RIGHT"),
        (2.0, "Hand rises slowly to temple / chin"),
        (2.8, "Jaw tightens — breathing held"),
        (3.5, "Alert tension — hold off-screen gaze"),
        (4.2, "Hand lowers — ease tension"),
        (5.0, "Return to start — loop end"),
    ],
}


def get_state(name: str) -> ActTwoState:
    key = name.strip().lower()
    if key not in STATES:
        raise ValueError(f"Unknown state '{name}'. Choose: {', '.join(STATES)}")
    return STATES[key]
