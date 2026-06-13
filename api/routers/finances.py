"""Auto-split from api/main.py — finances routes."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter()


def _finance_tx_row(body: FinanceTransactionCreate) -> dict[str, Any]:
    return {
        "date": body.tx_date.isoformat(),
        "type": body.type,
        "amount": body.amount,
        "currency": body.currency,
        "category": body.category,
        "project_id": body.project_id,
        "description": body.description,
        "is_recurring": body.is_recurring,
        "recurrence": body.recurrence if body.is_recurring else None,
    }


@router.get("/finances/transactions")
def list_finance_transactions(
    month: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}$"),
    type: str | None = Query(default=None, pattern="^(income|expense)$"),
    category: str | None = None,
    project_id: str | None = None,
) -> list[dict[str, Any]]:
    db = get_supabase()
    rows = fetch_finance_transactions(
        db,
        month=month,
        tx_type=type,
        category=category,
        project_id=project_id,
    )
    return attach_project_names(db, rows)


@router.post("/finances/transactions")
def create_finance_transaction(body: FinanceTransactionCreate) -> dict[str, Any]:
    db = get_supabase()
    return db.insert("transactions", _finance_tx_row(body))


@router.patch("/finances/transactions/{transaction_id}")
def update_finance_transaction(
    transaction_id: str,
    body: FinanceTransactionUpdate,
) -> dict[str, Any]:
    db = get_supabase()
    rows = db.select("transactions", filters={"id": transaction_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Transaction introuvable")

    updates = body.model_dump(exclude_unset=True, by_alias=True)
    if "date" in updates and updates["date"] is not None:
        updates["date"] = updates["date"].isoformat()
    if updates.get("is_recurring") is False:
        updates["recurrence"] = None
    if not updates:
        return rows[0]
    return db.update("transactions", transaction_id, updates)


@router.delete("/finances/transactions/{transaction_id}")
def delete_finance_transaction(transaction_id: str) -> dict[str, bool]:
    db = get_supabase()
    rows = db.select("transactions", filters={"id": transaction_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Transaction introuvable")
    db.delete("transactions", transaction_id)
    return {"ok": True}


