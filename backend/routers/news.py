from fastapi import APIRouter, Depends, Query
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from config.database_conf import get_db
from crud import news
from crud.news import search_news, get_search_count
from utils.response import success_response

router = APIRouter(prefix="/api/news", tags=["news"])

# 获取新闻分类列表
@router.get("/categories")
async def get_category(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    category = await news.get_category(skip, limit, db)
    return success_response(category)

# 获取新闻列表
@router.get("/list")
async def get_list(
        category_id: int = Query(..., alias = "categoryId"),
        page: int = 1,
        page_size: int = Query(10, alias = "pageSize", le=100),
        db: AsyncSession = Depends(get_db)
):
    offset = (page - 1) * page_size
    news_list = await news.get_list(db, category_id, offset, page_size)
    total = await news.get_count_ByCategory(db, category_id)
    # 判断是否有更多, 如果当前页的数据数量小于总条数,则表示有更多
    has_more = (offset + len(news_list)) < total
    return success_response({
            "list": news_list,
            "total": total,
            "hasMore": has_more
        }, "新闻列表获取成功")

# 获取新闻详情
@router.get("/detail")
async def get_detail(news_id: int = Query(..., alias="id"), db: AsyncSession = Depends(get_db)):
    news_detail = await news.get_detail(db, news_id)
    if not news_detail:
        raise HTTPException(status_code=404, detail="新闻不存在")
    views_res = await news.increase_views(db, news_detail.id)
    if not views_res:
        raise HTTPException(status_code=500, detail="新闻浏览量更新失败")
    related_news = await news.get_ralated_news(db, news_detail.id, news_detail.category_id)
    return success_response({
            "id": news_detail.id,
            "title": news_detail.title,
            "content": news_detail.content,
            "image": news_detail.image,
            "author": news_detail.author,
            "publishTime": news_detail.publish_time,
            "categoryId": news_detail.category_id,
            "views": news_detail.views,
            "relatedNews": related_news
        })


# 搜索新闻（按标题或摘要关键词模糊匹配）
@router.get("/search")
async def search(
    keyword: str = Query(..., min_length=1, max_length=50),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, alias="pageSize", le=100),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * page_size
    results = await search_news(db, keyword, offset, page_size)
    total = await get_search_count(db, keyword)
    has_more = (offset + len(results)) < total
    return success_response({
        "list": [
            {
                "id": n.id,
                "title": n.title,
                "description": n.description,
                "image": n.image,
                "author": n.author,
                "publishTime": n.publish_time,
                "categoryId": n.category_id,
                "views": n.views,
            }
            for n in results
        ],
        "total": total,
        "hasMore": has_more,
        "keyword": keyword,
    }, f'"{keyword}" 的搜索结果')