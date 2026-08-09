"""Hub CRUD — peeled from core.py (debt paydown)."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter()

@router.get("/robo/builds")
def list_robo_builds(project_id: str | None = None, limit: int = Query(default=20, le=100)) -> list[dict[str, Any]]:
    db = get_supabase()
    filters: dict[str, Any] = {}
    if project_id:
        filters["project_id"] = project_id
    return db.select("robo_builds", filters=filters or None, order_by="created_at", ascending=False, limit=limit)


@router.post("/robo/builds")
def create_robo_build(body: RoboBuildCreate) -> dict[str, Any]:
    db = get_supabase()
    return db.insert(
        "robo_builds",
        {
            "project_id": body.project_id,
            "branch": body.branch,
            "stage": body.stage,
            "version": body.version,
            "pcb_revision": body.pcb_revision,
            "firmware_version": body.firmware_version,
            "tests_passed_pct": body.tests_passed_pct,
            "open_issues": body.open_issues,
            "notes": body.notes,
        },
    )


@router.get("/robo/lab-tests")
def list_robo_lab_tests(project_id: str | None = None, category: str | None = None) -> list[dict[str, Any]]:
    db = get_supabase()
    filters: dict[str, Any] = {}
    if project_id:
        filters["project_id"] = project_id
    if category:
        filters["category"] = category
    return db.select("robo_lab_tests", filters=filters or None, order_by="created_at", ascending=False)


@router.post("/robo/lab-tests")
def create_robo_lab_test(body: RoboLabTestCreate) -> dict[str, Any]:
    db = get_supabase()
    return db.insert(
        "robo_lab_tests",
        {
            "project_id": body.project_id,
            "category": body.category,
            "name": body.name,
            "status": body.status,
            "measured_value": body.measured_value,
            "notes": body.notes,
        },
    )


@router.get("/robo/telemetry")
def list_robo_telemetry(project_id: str | None = None, limit: int = Query(default=20, le=100)) -> list[dict[str, Any]]:
    db = get_supabase()
    filters: dict[str, Any] = {}
    if project_id:
        filters["project_id"] = project_id
    return db.select("robo_telemetry", filters=filters or None, order_by="created_at", ascending=False, limit=limit)


@router.post("/robo/telemetry")
def create_robo_telemetry(body: RoboTelemetryCreate) -> dict[str, Any]:
    db = get_supabase()
    return db.insert(
        "robo_telemetry",
        {
            "project_id": body.project_id,
            "power_w": body.power_w,
            "temperature_c": body.temperature_c,
            "cpu_pct": body.cpu_pct,
            "battery_pct": body.battery_pct,
            "charge_cycles": body.charge_cycles,
            "autonomy_hours": body.autonomy_hours,
        },
    )


