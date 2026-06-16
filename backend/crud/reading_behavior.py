from datetime import datetime, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from models.reading_behavior import ReadingBehavior
from models.news import News


async def report_behavior(db: AsyncSession, user_id: int, news_id: int, action_type: str, duration: int = 0):
    record = ReadingBehavior(
        user_id=user_id, news_id=news_id,
        action_type=action_type, duration=duration,
    )
    db.add(record)
    await db.flush()
    await db.refresh(record)
    return record


async def get_user_stats(db: AsyncSession, user_id: int, days: int | None):
    """聚合用户在指定时间窗内的行为：阅读数、完成数、收藏数、分享数、总时长、按来源分布"""
    cutoff = datetime.now() - timedelta(days=days) if days else None

    base = select(ReadingBehavior).where(ReadingBehavior.user_id == user_id)
    if cutoff:
        base = base.where(ReadingBehavior.created_at >= cutoff)

    # 各行为计数 + duration 合计（仅 view 行为有时长）
    stmt_count = (
        select(ReadingBehavior.action_type, func.count(ReadingBehavior.id))
        .where(ReadingBehavior.user_id == user_id)
        .group_by(ReadingBehavior.action_type)
    )
    if cutoff:
        stmt_count = stmt_count.where(ReadingBehavior.created_at >= cutoff)
    rows = (await db.execute(stmt_count)).all()
    counts = {r[0]: r[1] for r in rows}

    # 总阅读时长
    stmt_dur = select(func.coalesce(func.sum(ReadingBehavior.duration), 0)).where(
        ReadingBehavior.user_id == user_id,
        ReadingBehavior.action_type == "view",
    )
    if cutoff:
        stmt_dur = stmt_dur.where(ReadingBehavior.created_at >= cutoff)
    total_duration = (await db.execute(stmt_dur)).scalar_one()

    # 按 source_platform 分布（基于 view 行为）
    stmt_src = (
        select(News.source_platform, func.count(ReadingBehavior.id))
        .join(News, News.id == ReadingBehavior.news_id)
        .where(ReadingBehavior.user_id == user_id, ReadingBehavior.action_type == "view")
        .group_by(News.source_platform)
    )
    if cutoff:
        stmt_src = stmt_src.where(ReadingBehavior.created_at >= cutoff)
    src_rows = (await db.execute(stmt_src)).all()
    by_source = {r[0] or "unknown": r[1] for r in src_rows}

    # 独立文章数（去重 news_id，仅 view 行为）
    stmt_distinct = (
        select(func.count(func.distinct(ReadingBehavior.news_id)))
        .where(ReadingBehavior.user_id == user_id, ReadingBehavior.action_type == "view")
    )
    if cutoff:
        stmt_distinct = stmt_distinct.where(ReadingBehavior.created_at >= cutoff)
    distinct_news = (await db.execute(stmt_distinct)).scalar_one()

    return {
        "viewCount": counts.get("view", 0),
        "completeCount": counts.get("complete", 0),
        "favoriteCount": counts.get("favorite", 0),
        "shareCount": counts.get("share", 0),
        "distinctNews": distinct_news,
        "totalDurationSec": int(total_duration),
        "bySource": by_source,
    }
