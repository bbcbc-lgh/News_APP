from datetime import datetime
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from models.search_history import SearchHistory


async def add_search(db: AsyncSession, user_id: int, query: str) -> SearchHistory:
    existing = await db.execute(
        select(SearchHistory).where(
            SearchHistory.user_id == user_id,
            SearchHistory.query == query,
        )
    )
    record = existing.scalar_one_or_none()
    if record:
        record.created_at = datetime.now()
    else:
        record = SearchHistory(user_id=user_id, query=query)
        db.add(record)
    await db.flush()
    await db.refresh(record)
    return record


async def get_search_history(db: AsyncSession, user_id: int, limit: int = 20):
    result = await db.execute(
        select(SearchHistory)
        .where(SearchHistory.user_id == user_id)
        .order_by(SearchHistory.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def delete_search_history_one(db: AsyncSession, user_id: int, history_id: int) -> bool:
    result = await db.execute(
        delete(SearchHistory).where(
            SearchHistory.id == history_id,
            SearchHistory.user_id == user_id,
        )
    )
    return result.rowcount > 0


async def clear_search_history(db: AsyncSession, user_id: int) -> int:
    result = await db.execute(
        delete(SearchHistory).where(SearchHistory.user_id == user_id)
    )
    return result.rowcount
