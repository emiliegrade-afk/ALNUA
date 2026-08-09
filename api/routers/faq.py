"""Hub CRUD — peeled from core.py (debt paydown)."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter()

@router.post("/faq")
def create_faq(body: FAQCreate) -> dict[str, Any]:
    bot = SAVBot()
    return bot.add_faq_entry(body.project_id, body.question, body.answer, body.tags)


@router.get("/faq")
def list_faq(project_id: str) -> list[dict[str, Any]]:
    bot = SAVBot()
    return bot.get_faq(project_id)


