from datetime import datetime
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from models.history import History
from models.news import News

# 添加历史记录，如果已存在则更新浏览时间
async def add_history(db: AsyncSession, user_id: int, news_id: int):
    result = await db.execute(
        select(History).where(History.user_id == user_id, History.news_id == news_id)
    )
    existing = result.scalar_one_or_none()
    if existing:
        existing.view_time = datetime.now()
        await db.flush()
        return existing
    hist = History(user_id=user_id, news_id=news_id)
    db.add(hist)
    # 确保hist.id在提交前可用
    await db.flush()
    # 刷新对象以获取数据库生成的ID和其他字段
    await db.refresh(hist)
    return hist

# 获取用户的历史记录列表，包含新闻信息和浏览时间
async def get_history(db: AsyncSession, user_id: int, skip: int = 0, limit: int = 10):
    stmt = (
        select(News, History.view_time.label("view_time"), History.id.label("history_id"))
        .join(History, History.news_id == News.id)
        .where(History.user_id == user_id)
        .order_by(History.view_time.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.all()

# 获取用户历史记录总数
async def get_history_count(db: AsyncSession, user_id: int) -> int:
    result = await db.execute(
        select(func.count(History.id)).where(History.user_id == user_id)
    )
    return result.scalar_one()

# 删除单条历史记录
async def delete_history(db: AsyncSession, user_id: int, history_id: int) -> bool:
    result = await db.execute(
        delete(History).where(History.id == history_id, History.user_id == user_id)
    )
    return result.rowcount > 0

# 清空用户的历史记录
async def clear_history(db: AsyncSession, user_id: int) -> int:
    result = await db.execute(
        delete(History).where(History.user_id == user_id)
    )
    return result.rowcount
