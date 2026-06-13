from fastapi import APIRouter, Depends, Query, BackgroundTasks
from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from config.database_conf import get_db
from crud import news
from crud.news import search_news, get_search_count
from utils.response import success_response

router = APIRouter(prefix="/api/news", tags=["news"])

# 固定数据源列表，与爬虫 source_platform 字段对应
SOURCES = [
    {"id": "all",        "name": "全部"},
    {"id": "hackernews", "name": "Hacker News"},
    {"id": "openai",     "name": "OpenAI Blog"},
    {"id": "google_ai",  "name": "Google AI Blog"},
    {"id": "mit",        "name": "MIT Tech Review"},
]

# 获取数据源列表
@router.get("/categories")
async def get_category():
    return success_response(SOURCES)

# 获取新闻列表
@router.get("/list")
async def get_list(
        source: str = Query("all"),
        page: int = 1,
        page_size: int = Query(10, alias="pageSize", le=100),
        db: AsyncSession = Depends(get_db)
):
    offset = (page - 1) * page_size
    src = None if source == "all" else source
    news_list = await news.get_list(db, src, offset, page_size)
    total = await news.get_count_by_source(db, src)
    has_more = (offset + len(news_list)) < total
    return success_response({
            "list": [
                {
                    "id": n.id,
                    "title": n.title,
                    "title_zh": n.title_zh,
                    "description": n.description,
                    "image": n.image,
                    "author": n.author,
                    "source_platform": n.source_platform,
                    "views": n.views,
                    "publish_time": str(n.publish_time),
                }
                for n in news_list
            ],
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
    related_news = await news.get_ralated_news(db, news_detail.id, news_detail.source_platform)
    return success_response({
            "id": news_detail.id,
            "title": news_detail.title,
            "titleZh": news_detail.title_zh,
            "description": news_detail.description,
            "descriptionZh": news_detail.description_zh,
            "content": news_detail.content,
            "contentZh": news_detail.content_zh,
            "image": news_detail.image,
            "author": news_detail.author,
            "source": news_detail.source_platform,
            "sourceUrl": news_detail.source_url,
            "publishTime": news_detail.publish_time,
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
                "title_zh": n.title_zh,
                "description": n.description,
                "image": n.image,
                "author": n.author,
                "source_platform": n.source_platform,
                "views": n.views,
                "publish_time": str(n.publish_time),
            }
            for n in results
        ],
        "total": total,
        "hasMore": has_more,
        "keyword": keyword,
    }, f'"{keyword}" 的搜索结果')


@router.post("/refresh")
async def refresh(background_tasks: BackgroundTasks):
    from main import _run_fetch
    background_tasks.add_task(_run_fetch)
    return success_r