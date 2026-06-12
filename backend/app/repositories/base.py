"""
app/repositories/base.py
────────────────────────────────────────────────────────────────────────────
Generic async repository base.

Why a repository layer?
───────────────────────
Services contain *business logic* (rules, orchestration, fine calculations).
Repositories contain *persistence logic* (SQL queries, ORM interactions).
Keeping them separate means:

  • Services can be unit-tested by injecting a fake/mock repository without
    needing a real database.
  • SQL queries are in one predictable place — not scattered across service
    functions.
  • Future changes to the ORM or query strategy affect only the repository,
    not the service.
"""
from __future__ import annotations

import logging
import uuid
from typing import Any, Generic, Sequence, Type, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import Base

logger = logging.getLogger(__name__)

ModelT = TypeVar("ModelT", bound=Base)  # type: ignore[type-arg]


class BaseRepository(Generic[ModelT]):
    """Provides get / list / add / delete for any ORM model."""

    def __init__(self, model: Type[ModelT], session: AsyncSession) -> None:
        self._model = model
        self._db = session

    # ── Primitives ────────────────────────────────────────────────────────────

    async def get_by_id(self, pk: uuid.UUID) -> ModelT | None:
        return await self._db.get(self._model, pk)

    async def get_by_field(self, field: str, value: Any) -> ModelT | None:
        col = getattr(self._model, field)
        return await self._db.scalar(select(self._model).where(col == value))

    async def count(self, *filters) -> int:
        q = select(func.count()).select_from(self._model)
        if filters:
            q = q.where(*filters)
        result = await self._db.scalar(q)
        return result or 0

    async def list_paged(
        self,
        *filters,
        order_by=None,
        page: int = 1,
        size: int = 20,
        options: list | None = None,
    ) -> tuple[Sequence[ModelT], int]:
        """Return (rows, total_count) for the given filters and page."""
        q = select(self._model)
        if filters:
            q = q.where(*filters)
        if options:
            for opt in options:
                q = q.options(opt)
        total = await self._db.scalar(select(func.count()).select_from(q.subquery()))
        if order_by is not None:
            q = q.order_by(order_by)
        q = q.offset((page - 1) * size).limit(size)
        rows = (await self._db.execute(q)).scalars().all()
        return rows, total or 0

    async def add(self, instance: ModelT) -> ModelT:
        self._db.add(instance)
        await self._db.flush()
        await self._db.refresh(instance)
        logger.debug("Added %s id=%s", self._model.__name__, getattr(instance, "id", "?"))
        return instance

    async def delete(self, instance: ModelT) -> None:
        await self._db.delete(instance)
        logger.debug("Deleted %s id=%s", self._model.__name__, getattr(instance, "id", "?"))

    async def flush_and_refresh(self, instance: ModelT) -> ModelT:
        await self._db.flush()
        await self._db.refresh(instance)
        return instance
