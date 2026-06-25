from sqlalchemy import func, select, update, or_, text
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from models.news import Category, News
from sqlalchemy import exists

FALLBACK_SOURCE_PLATFORMS = ("hackernews", "openai", "google_ai", "mit")
TIME_RANGE_DAYS = {"day": 1, "week": 7, "month": 30, "year": 365}


async def get_enabled_sources(db: AsyncSession) -> list[tuple[str, int]]:
    try:
        result = await db.execute(text("""
            SELECT platform, trust_tier
            FROM news_source
            WHERE enabled = 1
            ORDER BY trust_tier ASC, id ASC
        """))
        sources = [(row[0], int(row[1] or 3)) for row in result.all()]
        return sources or [(platform, 3) for platform in FALLBACK_SOURCE_PLATFORMS]
    except Exception:
        return [(platform, 3) for platform in FALLBACK_SOURCE_PLATFORMS]

# 分类列表
async def get_category(skip: int = 0, limit: int = 100, db: AsyncSession = None):
    result = await db.execute(select(Category).offset(skip).limit(limit))
    return result.scalars().all()

# 指定数据源的新闻列表（source=None 表示全部）
async def get_list(
        db: AsyncSession,
        source: str | None = None,
        skip: int = 0,
        limit: int = 10,
):
    if source is None:
        bucket_limit = skip + limit
        buckets: dict[str, list[int]] = {}
        for platform, trust_tier in await get_enabled_sources(db):
            trust_boost = max(0, 4 - trust_tier) * 8
            id_rows = await db.execute(text("""
                SELECT id
                FROM news
                WHERE source_platform = :platform
                ORDER BY
                  (
                    GREATEST(0, 72 - TIMESTAMPDIFF(HOUR, publish_time, NOW()))
                    + :trust_boost
                    + LEAST(COALESCE(source_score, 0), 500) / 50
                    + LEAST(COALESCE(source_comment_count, 0), 200) / 40
                  ) DESC,
                  publish_time DESC
                LIMIT :limit
            """), {"platform": platform, "trust_boost": trust_boost, "limit": bucket_limit})
            buckets[platform] = [row[0] for row in id_rows.all()]

        ids = []
        platforms = [platform for platform in buckets if buckets[platform]]
        for index in range(bucket_limit):
            for platform in platforms:
                if index < len(buckets[platform]):
                    ids.append(buckets[platform][index])
        ids = ids[skip:skip + limit]
        if not ids:
            return []
        result = await db.execute(
            select(News)
            .where(News.id.in_(ids))
            .order_by(text(f"FIELD(id, {','.join(str(i) for i in ids)})"))
        )
        return result.scalars().all()

    stmt = select(News)
    if source:
        stmt = stmt.where(News.source_platform == source)
    stmt = stmt.order_by(News.publish_time.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()

# 指定数据源的新闻总数
async def get_count_by_source(db: AsyncSession, source: str | None = None) -> int:
    stmt = select(func.count(News.id))
    if source:
        stmt = stmt.where(News.source_platform == source)
    result = await db.execute(stmt)
    return result.scalar_one()

def _build_search_where(keyword: str):
    """返回 (use_fulltext, where_clause_or_raw_sql_fragment)
    优先 MATCH AGAINST；LIKE 作为降级备用（由调用方决定）。
    实际上我们直接用 text() 在外层拼，这里只负责构造 ORM 过滤条件。
    """
    return or_(
        News.title.like(f"%{keyword}%"),
        News.title_zh.like(f"%{keyword}%"),
        News.description.like(f"%{keyword}%"),
        News.description_zh.like(f"%{keyword}%"),
    )


def _apply_common_filters(stmt, sources, time_range, tags):
    if sources:
        stmt = stmt.where(News.source_platform.in_(sources))
    if time_range and time_range != "all":
        days = TIME_RANGE_DAYS.get(time_range)
        if days:
            cutoff = datetime.now() - timedelta(days=days)
            stmt = stmt.where(News.publish_time >= cutoff)
    if tags:
        from models.topic_tag import NewsTopicTag, TopicTag
        subq = (
            select(NewsTopicTag.news_id)
            .join(TopicTag, TopicTag.id == NewsTopicTag.tag_id)
            .where(TopicTag.slug.in_(tags))
        )
        stmt = stmt.where(News.id.in_(subq))
    return stmt


# 关键词搜索新闻，优先 FULLTEXT，降级 LIKE
async def search_news(
        db: AsyncSession,
        keyword: str,
        skip: int = 0,
        limit: int = 10,
        sources: list[str] | None = None,
        time_range: str | None = None,
        tags: list[str] | None = None,
):
    try:
        # MATCH AGAINST with ngram parser（IN BOOLEAN MODE 支持短词）
        kw = keyword.replace("'", "''")
        base_where = f"MATCH(title, title_zh, description, description_zh) AGAINST ('{kw}' IN BOOLEAN MODE)"
        stmt = select(News).where(text(base_where))
        stmt = _apply_common_filters(stmt, sources, time_range, tags)
        stmt = stmt.order_by(News.publish_time.desc()).offset(skip).limit(limit)
        result = await db.execute(stmt)
        rows = result.scalars().all()
        if rows:
            return rows
    except Exception:
        pass

    # 降级：LIKE
    stmt = select(News).where(_build_search_where(keyword))
    stmt = _apply_common_filters(stmt, sources, time_range, tags)
    stmt = stmt.order_by(News.publish_time.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


# 关键词搜索结果总数
async def get_search_count(
        db: AsyncSession,
        keyword: str,
        sources: list[str] | None = None,
        time_range: str | None = None,
        tags: list[str] | None = None,
) -> int:
    try:
        kw = keyword.replace("'", "''")
        base_where = f"MATCH(title, title_zh, description, description_zh) AGAINST ('{kw}' IN BOOLEAN MODE)"
        stmt = select(func.count(News.id)).where(text(base_where))
        stmt = _apply_common_filters(stmt, sources, time_range, tags)
        result = await db.execute(stmt)
        count = result.scalar_one()
        if count > 0:
            return count
    except Exception:
        pass

    stmt = select(func.count(News.id)).where(_build_search_where(keyword))
    stmt = _apply_common_filters(stmt, sources, time_range, tags)
    result = await db.execute(stmt)
    return result.scalar_one()

# 按作者查询新闻列表
async def get_by_author(db: AsyncSession, author: str, skip: int = 0, limit: int = 10):
    stmt = select(News).where(News.author == author).order_by(News.publish_time.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_count_by_author(db: AsyncSession, author: str) -> int:
    stmt = select(func.count(News.id)).where(News.author == author)
    result = await db.execute(stmt)
    return result.scalar_one()


async def get_detail(db: AsyncSession, news_id: int):
    result = await db.execute(select(News).where(News.id == news_id))
    return result.scalar_one_or_none()

# 增加新闻的浏览量
async def increase_views (db: AsyncSession, news_id: int):
    result = await db.execute(update(News).where(News.id == news_id).values(views=News.views + 1))
    await db.commit()

    # 判断是否更新成功
    return result.rowcount > 0

# 获取新闻的关联新闻（同数据源）
async def get_ralated_news(db: AsyncSession, news_id: int, source_platform: str, limit: int = 5):
    stmt = select(News).where(
        News.source_platform == source_platform,
        News.id != news_id
    ).order_by(
        News.views.desc(),
        News.publish_time.desc()
    ).limit(limit)
    result = await db.execute(stmt)
    related_news = result.scalars().all()
    # 列表推导式,推导出核心数据,再return
    return[
        {"id": news_detail.id,
            "title": news_detail.title,
            "content": news_detail.content,
            "image": news_detail.image,
            "author": news_detail.author,
            "publishTime": news_detail.publish_time,
            "categoryId": news_detail.category_id,
            "views": news_detail.views
         } for news_detail in related_news
    ]
