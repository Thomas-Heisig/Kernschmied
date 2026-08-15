from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.models import UserContext
from app.auth.permissions import has_permission
from app.core.settings import settings
from app.hierarchy.repository import HierarchyRepository
from app.storage.database import get_session
from app.storage.models.file import File as FileModel
from app.storage.repositories.files import FileRepository
from app.storage.storage_utils import atomic_write_bytes, safe_storage_path

router = APIRouter()


class FileOut(BaseModel):
    id: str
    node_id: str | None
    owner_id: str | None
    name: str
    description: str | None = None
    mime_type: str | None = None
    size: int | None = None
    source: str | None = None
    created_at: datetime
    updated_at: datetime


class FileListResponse(BaseModel):
    items: list[FileOut]


class FilePatch(BaseModel):
    name: str | None = None
    description: str | None = None


SESSION_DEP = Depends(get_session)
USER_DEP = Depends(get_current_user)
NODE_FORM = Form(...)
FILE_DEFAULT = File(...)
NAME_FORM = Form(None)
DESCRIPTION_FORM = Form(None)


@router.get("/files", response_model=FileListResponse)
async def list_files(
    node_id: str | None = None,
    include_inherited: bool = False,
    session: AsyncSession = SESSION_DEP,
    user: UserContext = USER_DEP,
):
    if node_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="node_id required",
        )

    repo = FileRepository(session)
    rows = await repo.list_by_node(node_id)
    items = [FileOut(
        id=r.id,
        node_id=r.node_id,
        owner_id=r.owner_id,
        name=r.name,
        description=r.description,
        mime_type=r.mime_type,
        size=r.size,
        source=r.source,
        created_at=r.created_at,
        updated_at=r.updated_at,
    ) for r in rows]
    return FileListResponse(items=items)


@router.post("/files", response_model=FileOut, status_code=status.HTTP_201_CREATED)
async def upload_file(
    request: Request,
    node_id: str = NODE_FORM,
    file: UploadFile = FILE_DEFAULT,
    name: str | None = NAME_FORM,
    description: str | None = DESCRIPTION_FORM,
    session: AsyncSession = SESSION_DEP,
    user: UserContext = USER_DEP,
):
    # validate node exists
    hre = HierarchyRepository(session)
    node = await hre.get_node(node_id)
    if node is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="node not found",
        )

    # permission: allow when user has files.upload OR node belongs to user
    allowed = has_permission(user, "files.upload")
    if not allowed:
        md = dict(getattr(node, "node_metadata", {}) or {})
        entity_type = md.get("entity_type")
        entity_id = str(md.get("entity_id"))
        if not (entity_type == "user" and entity_id == user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="permission denied",
            )

    # prepare storage
    storage_root = (
        Path(settings.upload_directory)
        if settings.upload_directory
        else Path(settings.data_directory) / "files"
    )

    # stream-write to temp via UploadFile.file
    stream = iter(lambda: file.file.read(8192), b"")

    # create DB model first to reserve id
    fmodel = FileModel(
        node_id=node_id,
        owner_id=user.id,
        name=(name or file.filename),
        description=description,
        mime_type=(file.content_type or None),
        size=None,
        storage_path=None,
        source="upload",
    )
    session.add(fmodel)
    await session.flush()

    # compute final storage path using file id
    final_path = safe_storage_path(
        storage_root, node_id=node_id, file_id=fmodel.id
    )
    tmp_dir = None
    if settings.temporary_directory:
        tmp_dir = Path(settings.temporary_directory)
    try:
        path, size = atomic_write_bytes(final_path, stream, tmp_dir=tmp_dir)
    except Exception as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    # update model with storage path and size
    fmodel.storage_path = str(path.relative_to(storage_root))
    fmodel.size = int(size)
    session.add(fmodel)

    try:
        await session.commit()
    except Exception:
        await session.rollback()
        raise

    # post-commit: best-effort projection of node
    try:
        post = getattr(request.app.state, "post_commit_projection", None)
        if post is not None:
            await post.project_node(node.id)
    except Exception:
        # do not surface projection errors
        pass

    await session.refresh(fmodel)

    return FileOut(
        id=fmodel.id,
        node_id=fmodel.node_id,
        owner_id=fmodel.owner_id,
        name=fmodel.name,
        description=fmodel.description,
        mime_type=fmodel.mime_type,
        size=fmodel.size,
        source=fmodel.source,
        created_at=fmodel.created_at,
        updated_at=fmodel.updated_at,
    )


@router.get("/files/{file_id}/download")
async def download_file(
    file_id: str,
    session: AsyncSession = SESSION_DEP,
    user: UserContext = USER_DEP,
):
    repo = FileRepository(session)
    f = await repo.get(file_id)
    if f is None or f.deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    storage_root = (
        Path(settings.upload_directory)
        if settings.upload_directory
        else Path(settings.data_directory) / "files"
    )
    file_path = safe_storage_path(storage_root, node_id=(f.node_id or ""), file_id=f.id)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="file content missing",
        )

    return FileResponse(
        path=str(file_path),
        media_type=(f.mime_type or "application/octet-stream"),
        filename=f.name,
    )


@router.get("/files/{file_id}/preview")
async def preview_file(
    file_id: str,
    session: AsyncSession = SESSION_DEP,
    user: UserContext = USER_DEP,
):
    repo = FileRepository(session)
    f = await repo.get(file_id)
    if f is None or f.deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    storage_root = (
        Path(settings.upload_directory)
        if settings.upload_directory
        else Path(settings.data_directory) / "files"
    )
    file_path = safe_storage_path(storage_root, node_id=(f.node_id or ""), file_id=f.id)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="file content missing",
        )

    # only preview text types for now
    if f.mime_type and f.mime_type.startswith("text/"):
        try:
            text = file_path.read_text(encoding="utf-8", errors="replace")
            return JSONResponse({"id": f.id, "text": text})
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            ) from exc

    raise HTTPException(
        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        detail="preview not available for this file type",
    )


@router.patch("/files/{file_id}", response_model=FileOut)
async def patch_file(
    file_id: str,
    payload: FilePatch,
    session: AsyncSession = SESSION_DEP,
    user: UserContext = USER_DEP,
):
    repo = FileRepository(session)
    f = await repo.get(file_id)
    if f is None or f.deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    data: dict[str, Any] = {}
    if payload.name is not None:
        data["name"] = payload.name
    if payload.description is not None:
        data["description"] = payload.description

    updated = await repo.update_metadata(f, data)
    await session.commit()
    await session.refresh(updated)
    return FileOut(
        id=updated.id,
        node_id=updated.node_id,
        owner_id=updated.owner_id,
        name=updated.name,
        description=updated.description,
        mime_type=updated.mime_type,
        size=updated.size,
        source=updated.source,
        created_at=updated.created_at,
        updated_at=updated.updated_at,
    )


@router.delete("/files/{file_id}", status_code=status.HTTP_200_OK)
async def delete_file(
    file_id: str,
    session: AsyncSession = SESSION_DEP,
    user: UserContext = USER_DEP,
):
    repo = FileRepository(session)
    f = await repo.get(file_id)
    if f is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    await repo.mark_deleted(file_id)
    await session.commit()

    return {"status": "deleted"}
