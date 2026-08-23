"""Pydantic models — secretary / lounge / core agent requests."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SecretaryDraftEmailRequest(BaseModel):
    subject: str
    context: str
    recipient: str
    tone: str = "professionnel"
    language: str = "fr"


class SecretaryTriageRequest(BaseModel):
    emails: list[dict[str, str]]


class SecretaryDraftContractRequest(BaseModel):
    contract_type: str
    party_name: str
    scope: str
    duration: str
    compensation: str = ""
    special_clauses: str = ""


class SecretaryPlanMeetingRequest(BaseModel):
    participants: list[str]
    topic: str
    duration_minutes: int = 60
    constraints: str = ""


class SecretaryMeetingNotesRequest(BaseModel):
    meeting_title: str
    raw_notes: str
    participants: list[str]


class MilestoneCreateRequest(BaseModel):
    title: str
    date_iso: str
    pole: str = ""
    description: str = ""


class MilestoneUpdateRequest(BaseModel):
    title: str | None = None
    date_iso: str
    pole: str | None = None
    description: str | None = None


class MilestoneValidateRequest(BaseModel):
    validated: bool = True


class ScoreAddRequest(BaseModel):
    agent_id: str
    action: str = Field(
        pattern="^(task_completed|task_validated|feature_shipped|bug_found_critical|bug_fixed|review_approved|document_produced|insight_actioned|custom)$"
    )
    points: int | None = Field(default=None, ge=1, le=500)
    note: str = ""


class LoungeScoreAddRequest(BaseModel):
    agent_id: str
    action: str = Field(
        pattern="^(session_completed|challenge_won|duel_won|collab_completed|custom)$"
    )
    points: int | None = Field(default=None, ge=1, le=500)
    note: str = ""


class LoungeSessionStartRequest(BaseModel):
    agent_id: str = Field(min_length=1, max_length=64)
    activity: str = Field(
        default="puzzle",
        pattern="^(arcade|strategy|puzzle|code_challenge|simulation|exploration|creative)$",
    )
    puzzle_id: str | None = Field(default=None, max_length=64)
    challenge_id: str | None = Field(default=None, max_length=64)
    run_now: bool = False


class LoungeSessionCompleteRequest(BaseModel):
    answer: str = Field(min_length=1, max_length=2000)


class LoungeProposeRequest(BaseModel):
    session_id: str = Field(min_length=8, max_length=64)
    dept: str = Field(
        pattern="^(app|rd|gaming|robo|marketing|hub|finances|analytics)$"
    )
    summary: str = Field(min_length=8, max_length=2000)
    project_id: str | None = None
    agent_id: str | None = Field(default=None, max_length=64)


class AgentInstructionRequest(BaseModel):
    instruction: str


class GameDirectorLoreSearchRequest(BaseModel):
    query: str
    project: str | None = None
    limit: int = 5


class RndAgentResearchRequest(BaseModel):
    query: str
    context: str = ""


class RndAgentPrototypeRequest(BaseModel):
    idea: str
    context: str = ""


class CodingCoachTeachRequest(BaseModel):
    message: str
    workspace: str = "sandbox"
    file_path: str | None = None
    file_content: str | None = None


class CodingCoachExerciseRequest(BaseModel):
    topic: str
    level: str = "débutant"
