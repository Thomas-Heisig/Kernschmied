from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.storage.database import get_session
from app.database.models.user_role import RoleModel

router = APIRouter()


class RoleItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    label: str = Field(..., alias="display_name")
    description: str | None = None
    is_system: bool = False
    assignable: bool = True


class RolesResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: str = "1.0"
    items: list[RoleItem]


@router.get("/", response_model=RolesResponse)
async def list_roles(session: AsyncSession = Depends(get_session)):
    stmt = await session.execute("SELECT id, name, display_name, description, is_system, assignable FROM roles ORDER BY name")
    rows = stmt.fetchall()
    items = []
    for r in rows:
        items.append(
            RoleItem(
                id=r[0], name=r[1], display_name=r[2], description=r[3], is_system=bool(r[4]), assignable=bool(r[5])
            )
        )

    return RolesResponse(items=items)
