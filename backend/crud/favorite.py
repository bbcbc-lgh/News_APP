from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from models.favorite import Favorite
from models.news import News

# 检查用户是否已收藏某条新闻，返回布尔值
async def check_favorite(db: AsyncSession, user_id: int, news_id: int) -> bool:
    result = await db.execute(
        select(Favorite).where(Favorite.user_id == user_id, Favorite.news_id == news_id)
    )
    return result.scalar_one_or_none() is not None

# 添加收藏记录，并返回新创建的 Favorite 对象
async def add_favorite(db: AsyncSession, user_id: int, news_id: int):
    fav = Favorite(user_id=user_id, news_id=news_id)
    db.add(fav)
    # 在提交之前刷新对象以获取数据库生成的 ID 和时间戳等字段
    await db.flush()
    # 刷新对象以确保我们获得了数据库生成的 ID 和时间戳等字段
    await db.refresh(fav)
    return fav

# 移除收藏记录，返回是否成功删除
async def remove_favorite(db: AsyncSession, user_id: int, news_id: int) -> bool:
    result = await db.execute(
        delete(Favorite).where(Favorite.user_id == user_id, Favorite.news_id == news_id)
    )
    return result.rowcount > 0

# 获取用户的收藏列表，支持分页
async def get_favorites(db: AsyncSession, user_id: int, skip: int = 0, limit: int = 10):
    stmt = (
        select(News, Favorite.created_at.label("favorite_time"))
        .join(Favorite, Favorite.news_id == News.id)
        .where(Favorite.user_id == user_id)
        .order_by(Favorite.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.all()             # 返回一个包含新闻对象和收藏时间的列表

# 获取用户收藏的总数，用于分页等功能
async def get_favorites_count(db: AsyncSession, user_id: int) -> int:
    result = await db.execute(
        select(func.count(Favorite.id)).where(Favorite.user_id == user_id)
    )
    return result.scalar_one()

# 清空用户的所有收藏记录，返回删除的记录数
async def clear_favorites(db: AsyncSession, user_id: int) -> int:
    result = await db.execute(
        delete(Favorite).where(Favorite.user_id == user_id)
    )
    return result.rowcount
