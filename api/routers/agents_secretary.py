"""Secretary agent + milestone routes."""

from __future__ import annotations

from api.route_common import *  # noqa: F403
from api.routers.agents_pole_helpers import clean_agent_text

router = APIRouter()


@router.post("/agents/secretary/draft-email")
def secretary_draft_email(body: SecretaryDraftEmailRequest) -> dict[str, Any]:
    return SecretaryAgent().draft_email(
        body.subject, clean_agent_text(body.context), body.recipient, body.tone, body.language
    )


@router.post("/agents/secretary/triage-emails")
def secretary_triage_emails(body: SecretaryTriageRequest) -> dict[str, Any]:
    emails = [
        {
            **e,
            "body": clean_agent_text(e.get("body", "")),
            "subject": clean_agent_text(e.get("subject", ""), max_length=500),
        }
        for e in body.emails
    ]
    return SecretaryAgent().triage_emails(emails)


@router.post("/agents/secretary/draft-contract")
def secretary_draft_contract(body: SecretaryDraftContractRequest) -> dict[str, Any]:
    return SecretaryAgent().draft_contract(
        body.contract_type,
        body.party_name,
        clean_agent_text(body.scope),
        body.duration,
        body.compensation,
        clean_agent_text(body.special_clauses),
    )


@router.post("/agents/secretary/plan-meeting")
def secretary_plan_meeting(body: SecretaryPlanMeetingRequest) -> dict[str, Any]:
    return SecretaryAgent().plan_meeting(
        body.participants,
        clean_agent_text(body.topic, max_length=500),
        body.duration_minutes,
        clean_agent_text(body.constraints),
    )


@router.post("/agents/secretary/meeting-notes")
def secretary_meeting_notes(body: SecretaryMeetingNotesRequest) -> dict[str, Any]:
    return SecretaryAgent().write_meeting_notes(
        body.meeting_title, clean_agent_text(body.raw_notes), body.participants
    )


@router.get("/agents/secretary/milestones")
def secretary_list_milestones(days_ahead: int = 120) -> dict[str, Any]:
    from services.milestones import list_upcoming_milestones

    return {"milestones": list_upcoming_milestones(days_ahead=days_ahead)}


@router.post("/agents/secretary/milestones")
def secretary_create_milestone(body: MilestoneCreateRequest) -> dict[str, Any]:
    from services.milestones import create_milestone

    return create_milestone(
        clean_agent_text(body.title, max_length=200),
        body.date_iso,
        pole=body.pole,
        description=clean_agent_text(body.description),
    )


@router.patch("/agents/secretary/milestones/{event_id}")
def secretary_update_milestone(event_id: str, body: MilestoneUpdateRequest) -> dict[str, Any]:
    from services.milestones import update_milestone

    return update_milestone(
        event_id,
        title=clean_agent_text(body.title, max_length=200) if body.title is not None else None,
        date_iso=body.date_iso,
        pole=body.pole,
        description=clean_agent_text(body.description) if body.description is not None else None,
    )


@router.post("/agents/secretary/milestones/{event_id}/validate")
def secretary_validate_milestone(event_id: str, body: MilestoneValidateRequest) -> dict[str, Any]:
    from services.milestones import set_milestone_validated

    return set_milestone_validated(event_id, body.validated)
