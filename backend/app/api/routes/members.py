import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.schemas import MemberCreate, MemberOut, MemberUpdate, PagedResponse
from app.services import member_service

router = APIRouter(prefix="/members", tags=["Members"])


@router.post("", response_model=MemberOut, status_code=status.HTTP_201_CREATED)
async def create_member(body: MemberCreate, db: AsyncSession = Depends(get_db)):
    """Register a new library member."""
    member = await member_service.create_member(db, body)
    out = MemberOut.model_validate(member)
    out.active_loans = 0
    return out


@router.get("", response_model=PagedResponse[MemberOut])
async def list_members(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    active_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    """List all members with optional filtering."""
    return await member_service.list_members(db, page, size, search, active_only)


@router.get("/{member_id}", response_model=MemberOut)
async def get_member(member_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Fetch a single member by ID."""
    member = await member_service.get_member(db, member_id)
    out = MemberOut.model_validate(member)
    return out


@router.patch("/{member_id}", response_model=MemberOut)
async def update_member(
    member_id: uuid.UUID,
    body: MemberUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update member details."""
    member = await member_service.update_member(db, member_id, body)
    return MemberOut.model_validate(member)


@router.delete("/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_member(member_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Remove a member (only allowed if no active loans)."""
    await member_service.delete_member(db, member_id)
