"""Hub CRUD — peeled from core.py (debt paydown)."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter()

def _fetch_all_analytics(db, project_id: str | None = None) -> list[dict[str, Any]]:
    filters = {"project_id": project_id} if project_id else None
    return db.select(
        "analytics",
        filters=filters,
        order_by="date",
        ascending=True,
        limit=2000,
    )


def _fetch_transactions(db, project_id: str | None = None) -> list[dict[str, Any]]:
    filters = {"project_id": project_id} if project_id else None
    return db.select(
        "transactions",
        filters=filters,
        order_by="date",
        ascending=True,
        limit=2000,
    )


def _kpi_metric(
    rows: list[dict[str, Any]],
    metric_name: str,
    project_id: str | None,
    use_sum_in_month: bool = False,
) -> dict[str, Any]:
    """Calcule valeur du mois courant + variation vs mois précédent."""
    cur_start, cur_end = month_bounds()
    prev_start, prev_end = previous_month_bounds()

    if use_sum_in_month:
        current = sum_metric_in_range(rows, metric_name, cur_start, cur_end, project_id)
        previous = sum_metric_in_range(rows, metric_name, prev_start, prev_end, project_id)
    else:
        cur_latest = latest_values_by_project(rows, metric_name, cur_end)
        prev_latest = latest_values_by_project(rows, metric_name, prev_end)
        if project_id:
            current = cur_latest.get(project_id)
            previous = prev_latest.get(project_id)
        else:
            current = sum(cur_latest.values()) if cur_latest else None
            previous = sum(prev_latest.values()) if prev_latest else None

    return {
        "value": current if current is not None else None,
        "change_pct": pct_change(current, previous),
    }


@router.get("/analytics")
def list_analytics(
    project_id: str | None = None,
    metric_name: str | None = None,
    period: str = Query(default="30d"),
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[dict[str, Any]]:
    db = get_supabase()
    if start_date and end_date:
        start, end = start_date, end_date
    else:
        start, end = parse_period(period)

    rows = _fetch_all_analytics(db, project_id)
    if metric_name:
        rows = [r for r in rows if r.get("metric_name") == metric_name]
    rows = filter_by_date_range(rows, start, end)

    projects = {p["id"]: p["name"] for p in db.select("projects")}
    for row in rows:
        row["project_name"] = projects.get(row.get("project_id"), "Projet")
    return rows


@router.get("/analytics/summary")
def analytics_summary(project_id: str | None = None) -> dict[str, Any]:
    db = get_supabase()
    rows = _fetch_all_analytics(db, project_id)
    tx_rows = _fetch_transactions(db, project_id)

    cur_start, cur_end = month_bounds()
    prev_start, prev_end = previous_month_bounds()

    revenue_cur = sum(
        float(t["amount"])
        for t in tx_rows
        if t.get("type") in ("revenue", "income")
        and cur_start <= date.fromisoformat(str(t["date"])[:10]) <= cur_end
    )
    revenue_prev = sum(
        float(t["amount"])
        for t in tx_rows
        if t.get("type") in ("revenue", "income")
        and prev_start <= date.fromisoformat(str(t["date"])[:10]) <= prev_end
    )

    return {
        "downloads": _kpi_metric(rows, "downloads", project_id, use_sum_in_month=True),
        "subscriptions": _kpi_metric(rows, "subscriptions", project_id),
        "mrr": _kpi_metric(rows, "mrr", project_id),
        "churn": _kpi_metric(rows, "churn", project_id),
        "web_visitors": _kpi_metric(rows, "web_visitors", project_id, use_sum_in_month=True),
        "revenue_month": {
            "value": revenue_cur if revenue_cur else None,
            "change_pct": pct_change(revenue_cur, revenue_prev),
        },
    }


@router.get("/analytics/revenue")
def analytics_revenue(
    project_id: str | None = None,
    period: str = Query(default="30d"),
) -> dict[str, Any]:
    db = get_supabase()
    start, end = parse_period(period)
    tx_rows = filter_by_date_range(_fetch_transactions(db, project_id), start, end)
    analytics_rows = filter_by_date_range(_fetch_all_analytics(db, project_id), start, end)

    months: dict[str, dict[str, float]] = {}

    for tx in tx_rows:
        d = date.fromisoformat(str(tx["date"])[:10])
        key = d.strftime("%Y-%m")
        bucket = months.setdefault(key, {"revenue": 0.0, "expense": 0.0, "mrr": 0.0})
        if tx.get("type") in ("revenue", "income"):
            bucket["revenue"] += float(tx["amount"])
        else:
            bucket["expense"] += float(tx["amount"])

    for row in analytics_rows:
        if row.get("metric_name") != "mrr":
            continue
        d = date.fromisoformat(str(row["date"])[:10])
        key = d.strftime("%Y-%m")
        bucket = months.setdefault(key, {"revenue": 0.0, "expense": 0.0, "mrr": 0.0})
        bucket["mrr"] = max(bucket["mrr"], float(row["value"]))

    series = [
        {"month": k, **v}
        for k, v in sorted(months.items())
    ]
    return {"months": series}


@router.post("/analytics")
def create_analytics_metric(body: AnalyticsCreate) -> dict[str, Any]:
    db = get_supabase()
    return db.insert(
        "analytics",
        {
            "project_id": body.project_id,
            "metric_name": body.metric_name,
            "value": body.value,
            "date": (body.record_date or date.today()).isoformat(),
            "source": body.source,
        },
    )


@router.post(
    "/transactions",
    deprecated=True,
    description="Legacy alias — use POST /finances/transactions.",
)
def create_transaction(body: TransactionCreate) -> dict[str, Any]:
    db = get_supabase()
    tx_type = "income" if body.type == "revenue" else body.type
    return db.insert(
        "transactions",
        {
            "project_id": body.project_id,
            "type": tx_type,
            "amount": body.amount,
            "currency": body.currency,
            "category": body.category,
            "description": body.description,
            "date": (body.transaction_date or date.today()).isoformat(),
            "is_recurring": body.is_recurring,
            "recurrence": body.recurrence,
        },
    )


