"""
Hacker News 采集器，通过官方 Firebase JSON API 获取 AI 相关文章
"""
import asyncio
import httpx
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from crawler.base import save_news
from crud.topic_tag import infer_and_tag
from crawler.filters import is_ai_related
from utils.content_guard import clean_content

HN_API = "https://hacker-news.firebaseio.com/v0"
FETCH_TOP_N = 100


async def _get_top_ids(client: httpx.AsyncClient) -> list[int]:
    resp = await client.get(f"{HN_API}/topstories.json", timeout=10)
    resp.raise_for_status()
    return resp.json()[:FETCH_TOP_N]


async def _get_item(client: httpx.AsyncClient, item_id: int) -> dict | None:
    try:
        resp = await client.get(f"{HN_API}/item/{item_id}.json", timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


CONCURRENCY = 15  # 并发拉取上限，避免触发限流


async def _process_item(client: httpx.AsyncClient, db: AsyncSession, item_id: int, sem: asyncio.Semaphore) -> bool:
    """拉取单条 story 并入库，返回是否新增"""
    async with sem:
        item = await _get_item(client, item_id)
        if not item or item.get("type") != "story":
            return False
        title = (item.get("title") or "").strip()
        url = item.get("url") or f"https://news.ycombinator.com/item?id={item_id}"
        if not title or not is_ai_related(title):
            return False
        pub_time = datetime.fromtimestamp(item["time"]) if item.get("time") else datetime.now()
        content = clean_content(item.get("text", ""), min_chars=80, max_chars=3000)
        news_id = await save_news(
            db,
            title=title,
            description="",
            content=content,
            image="",
            author=item.get("by", ""),
            source_url=url,
            source_platform="hackernews",
            publish_time=pub_time,
            category_id=1,
            external_id=str(item_id),
            source_score=int(item.get("score") or 0),
            source_comment_count=int(item.get("descendants") or 0),
        )
        if news_id:
            await infer_and_tag(db, news_id, title)
        return news_id


async def fetch_hn(db: AsyncSession) -> int:
    """采集 Hacker News 热门中的 AI 相关文章，并发拉取，返回新增条数"""
    count = 0
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            ids = await _get_top_ids(client)
            sem = asyncio.Semaphore(CONCURRENCY)
            tasks = [_process_item(client, db, item_id, sem) for item_id in ids]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            count = sum(1 for r in results if isinstance(r, int) and not isinstance(r, bool))
    except Exception as e:
        print(f"[hackernews] 采集失败: {e}")
    print(f"[hackernews] 新增 {count} 条")
    return count
