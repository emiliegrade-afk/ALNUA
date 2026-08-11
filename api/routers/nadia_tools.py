"""Nadia docs + PC housekeeper API."""

from __future__ import annotations

from api.route_common import *  # noqa: F403
from services.input_sanitizer import sanitize_user_input

router = APIRouter(tags=["nadia-tools"])


class DocCreateRequest(BaseModel):
    title: str
    content: str = ""
    doc_type: str = "note"


class DocUpdateRequest(BaseModel):
    content: str
    title: str | None = None


class HousekeepApplyRequest(BaseModel):
    proposals: list[dict[str, Any]] | None = None
    dry_run: bool = False


class QuarantineRequest(BaseModel):
    paths: list[str]


@router.get("/nadia/docs")
def nadia_list_docs() -> dict[str, Any]:
    from services.nadia_docs import list_documents

    return {"documents": list_documents()}


@router.post("/nadia/docs")
def nadia_create_doc(body: DocCreateRequest) -> dict[str, Any]:
    from services.nadia_docs import create_document

    title = sanitize_user_input(body.title, max_length=200, redact_pii_enabled=False)
    content = sanitize_user_input(body.content or "", max_length=50000, redact_pii_enabled=False)
    return create_document(title, content, doc_type=body.doc_type or "note")


@router.get("/nadia/docs/{doc_id}")
def nadia_read_doc(doc_id: str) -> dict[str, Any]:
    from services.nadia_docs import read_document

    doc = read_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="document introuvable")
    return doc


@router.put("/nadia/docs/{doc_id}")
def nadia_update_doc(doc_id: str, body: DocUpdateRequest) -> dict[str, Any]:
    from services.nadia_docs import update_document

    content = sanitize_user_input(body.content, max_length=50000, redact_pii_enabled=False)
    title = (
        sanitize_user_input(body.title, max_length=200, redact_pii_enabled=False)
        if body.title
        else None
    )
    doc = update_document(doc_id, content, title=title)
    if not doc:
        raise HTTPException(status_code=404, detail="document introuvable")
    return doc


@router.post("/nadia/docs/{doc_id}/export")
def nadia_export_doc(doc_id: str, fmt: str = "txt") -> dict[str, Any]:
    from services.nadia_docs import export_docx, export_txt

    path = export_docx(doc_id) if fmt.lower() == "docx" else export_txt(doc_id)
    if not path:
        raise HTTPException(
            status_code=404 if fmt.lower() != "docx" else 501,
            detail="export impossible (doc manquant ou python-docx absent)",
        )
    return {"path": str(path), "format": fmt.lower()}


@router.get("/housekeeper/status")
def housekeeper_status() -> dict[str, Any]:
    from agents.housekeeper_agent import HousekeeperAgent

    return HousekeeperAgent().status()


@router.post("/housekeeper/scan")
def housekeeper_scan(extra_roots: list[str] | None = None) -> dict[str, Any]:
    from agents.housekeeper_agent import HousekeeperAgent

    return HousekeeperAgent().scan(extra_roots)


@router.post("/housekeeper/propose")
def housekeeper_propose() -> dict[str, Any]:
    from agents.housekeeper_agent import HousekeeperAgent

    return HousekeeperAgent().propose()


@router.post("/housekeeper/apply")
def housekeeper_apply(body: HousekeepApplyRequest) -> dict[str, Any]:
    from agents.housekeeper_agent import HousekeeperAgent

    return HousekeeperAgent().apply(body.proposals, dry_run=body.dry_run)


@router.post("/housekeeper/quarantine")
def housekeeper_quarantine(body: QuarantineRequest) -> dict[str, Any]:
    from agents.housekeeper_agent import HousekeeperAgent

    return HousekeeperAgent().quarantine(body.paths)


@router.post("/housekeeper/purge")
def housekeeper_purge(confirm: bool = False) -> dict[str, Any]:
    from services.pc_housekeeper import purge_quarantine

    return purge_quarantine(confirm=confirm)


@router.post("/housekeeper/autonomy")
def housekeeper_autonomy(enabled: bool) -> dict[str, Any]:
    from services.pc_housekeeper import set_autonomy

    return set_autonomy(enabled)
