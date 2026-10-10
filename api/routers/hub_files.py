"""Hub user file library API — uploads reusable in Live / Secretary."""

from __future__ import annotations

from typing import Any

from fastapi.responses import Response

from api.route_common import *  # noqa: F403

router = APIRouter(prefix="/hub/files", tags=["hub-files"])


@router.post("", status_code=201)
async def hub_file_upload(
    file: UploadFile = File(...),
    source: str = Form(default="upload"),
) -> dict[str, Any]:
    from services.hub_user_files import get_store

    data = await file.read()
    try:
        record = get_store().save_bytes(
            data,
            file.filename or "file.txt",
            file.content_type or "text/plain",
            source=source.strip() or "upload",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return record.to_dict()


@router.get("")
def hub_file_list(
    q: str = "",
    source: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    from services.hub_user_files import get_store

    files = get_store().list_files(query=q, source=source, limit=limit)
    return {"files": [f.to_dict() for f in files]}


@router.get("/{file_id}")
def hub_file_meta(file_id: str) -> dict[str, Any]:
    from services.hub_user_files import get_store

    record = get_store().get(file_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Fichier introuvable")
    return record.to_dict()


@router.get("/{file_id}/content")
def hub_file_content(file_id: str) -> Response:
    from services.hub_user_files import get_store

    record = get_store().get(file_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Fichier introuvable")
    try:
        data = get_store().read_bytes(file_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return Response(
        content=data,
        media_type=record.content_type or "text/plain",
        headers={"Content-Disposition": f'inline; filename="{record.name}"'},
    )


@router.delete("/{file_id}", status_code=204, response_class=Response)
def hub_file_delete(file_id: str) -> Response:
    from services.hub_user_files import get_store

    if not get_store().delete(file_id):
        raise HTTPException(status_code=404, detail="Fichier introuvable")
    return Response(status_code=204)
