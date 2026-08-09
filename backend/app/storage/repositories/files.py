from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.storage.models.file import File
from app.storage.repositories.base import Repository


class FileRepository(Repository[File]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)

    async def get(self, file_id: str) -> File | None:
        return await self.session.get(File, file_id)

    async def add_file(self, file: File) -> File:
        self.session.add(file)
        await self.session.flush()
        await self.session.refresh(file)
        return file

    async def list_by_node(self, node_id: str) -> Sequence[File]:
        stmt = (
            select(File)
            .where(File.node_id == node_id)
            .where(File.deleted.is_(False))
        )
        result = await self.session.scalars(stmt)
        return result.all()

    async def mark_deleted(self, file_id: str) -> None:
        f = await self.session.get(File, file_id)
        if f is None:
            return
        f.deleted = True
        self.session.add(f)
        await self.session.flush()

    async def update_metadata(self, file: File, data: dict[str, Any]) -> File:
        for k, v in data.items():
            if hasattr(file, k):
                setattr(file, k, v)
        self.session.add(file)
        await self.session.flush()
        await self.session.refresh(file)
        return file


__all__ = ["FileRepository"]
