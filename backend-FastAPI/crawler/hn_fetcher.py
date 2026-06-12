"""
Hacker News 采集器，通过官方 Firebase JSON API 获取 AI 相关文章
"""
import httpx
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from crawler.base import save_news
from crawler.filters import is_ai_related

HN_API = "https://hacker-news.firebaseio.com/v0"
FETCH_TOP_N = 100  # 每次取前100条热门，过滤后入库


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


async def fetch_hn(db: AsyncSession) -> int:
    """采集 Hacker News 热门中的 AI 相关文章，返回新增条数"""
    count = 0
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            ids = await _get_top_ids(client)
            for item_id in ids:
                item = await _get_item(client, item_id)
                if not item:
                    continue
                # 只处理普通文章（type=story），跳过 Ask HN / Job 等
                if item.get("type") != "story":
                    continue
                title = (item.get("title") or "").strip()
                url = item.get("url", "")
                if not title or not is_ai_related(title):
                    continue
                pub_time = datetime.fromtimestamp(item["time"]) if item.get("time") else datetime.now()
                saved = await save_news(
                    db,
                    title=title,
                    description=f"HN 评论数：{item.get('descendants', 0)}",
                    content="",
                    image="",
                    author=item.get("by", ""),
                    source_url=url,
                    source_platform="hackernews",
                    publish_time=pub_time,
                    category_id=1,
                )
                if saved:
                    count += 1
    except Exception as e:
        print(f"[hackernews] 采集失败: {e}")
    print(f"[hackernews] 新增 {count} 条")
    return count
