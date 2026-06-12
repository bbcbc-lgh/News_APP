from sqlalchemy import func, select, update, or_
from sqlalchemy.ext.asyncio import AsyncSession
from models.news import Category, News

# 分类列表
async def get_category(skip: int = 0, limit: int = 100, db: AsyncSession = None):
    result = await db.execute(select(Category).offset(skip).limit(limit))
    return result.scalars().all()

# 指定分类的新闻列表
async def get_list(
        db: AsyncSession,
        category_id: int,
        skip: int = 0,
        limit: int = 10,
):
    result = await db.execute(select(News).where(News.category_id == category_id).offset(skip).limit(limit))
    return result.scalars().all()


# 关键词搜索新闻（标题或摘要模糊匹配），支持跨分类
async def search_news(
        db: AsyncSession,
        keyword: str,
        skip: int = 0,
        limit: int = 10,
):
    stmt = select(News).where(
        or_(
            News.title.like(f"%{keyword}%"),
            News.description.like(f"%{keyword}%"),
        )
    ).order_by(News.publish_time.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


# 关键词搜索结果总数
async def get_search_count(db: AsyncSession, keyword: str) -> int:
    result = await db.execute(
        select(func.count(News.id)).where(
            or_(
                News.title.like(f"%{keyword}%"),
                News.description.like(f"%{keyword}%"),
            )
        )
    )
    return result.scalar_one()

# 分类的个数
async def get_count_ByCategory (db: AsyncSession, category_id: int):
    result = await db.execute(select(func.count(News.id)).where(News.category_id == category_id))
    return result.scalar_one() # 只能有一个结果,否则报错

# 新闻详情
async def get_detail (db: AsyncSession, news_id: int):
    result = await db.execute(select(News).where(News.id == news_id))
    return result.scalar_one_or_none()

# 增加新闻的浏览量
async def increase_views (db: AsyncSession, news_id: int):
    result = await db.execute(update(News).where(News.id == news_id).values(views=News.views + 1))
    await db.commit()

    # 判断是否更新成功
    return result.rowcount > 0

# 获取新闻的关联新闻
async def get_ralated_news (db: AsyncSession, news_id: int, category_id: int, limit: int = 5):
    # order_by代表排序
    stmt = select(News).where(
        News.category_id == category_id,
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