"""
Hacker News 采集器，通过官方 Firebase JSON API 获取 AI 相关文章
"""
import re
import asyncio
import httpx
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from crawler.base import save_news
from crawler.filters import is_ai_related

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


async def _fetch_page_content(client: httpx.AsyncClient, url: str) -> tuple[str, str]:
    """抓取原文页面，返回 (image_url, content_text)"""
    if not url:
        return "", ""
    try:
        resp = await client.get(url, timeout=8, follow_redirects=True,
                                headers={"User-Agent": "Mozilla/5.0"})
        html = resp.text[:200000]
        image = ""
        # og:image
        m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html, re.IGNORECASE)
        if not m:
            m = re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']', html, re.IGNORECASE)
        if m:
            img = m.group(1).strip()
            if img.startswith("http"):
                image = img
        if not image:
            m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', html, re.IGNORECASE)
            if m:
                img = m.group(1).strip()
                if img.startswith("http"):
                    image = img

        # 提取正文：优先 <article>，其次 <main>，再次 <div class="content/post/entry">
        content = ""
        for pattern in [
            r'<article[^>]*>([\s\S]*?)</article>',
            r'<main[^>]*>([\s\S]*?)</main>',
            r'<div[^>]+class=["\'][^"\']*(?:post-content|article-body|entry-content|story-body)[^"\']*["\'][^>]*>([\s\S]*?)</div>',
        ]:
            m = re.search(pattern, html, re.IGNORECASE)
            if m:
                raw = m.group(1)
                # 去除脚本、样式、导航等无关标签
                raw = re.sub(r'<(script|style|nav|header|footer|aside|figure)[^>]*>[\s\S]*?</\1>', '', raw, flags=re.IGNORECASE)
                # 剥离所有 HTML 标签，保留文本
                text_content = re.sub(r'<[^>]+>', ' ', raw)
                # 压缩空白
                text_content = re.sub(r'\s{3,}', '\n\n', text_content).strip()
                if len(text_content) > 200:
                    content = text_content[:8000]
                    break
        return image, content
    except Exception:
        return "", ""


CONCURRENCY = 15  # 并发拉取上限，避免触发限流


async def _process_item(client: httpx.AsyncClient, db: AsyncSession, item_id: int, sem: asyncio.Semaphore) -> bool:
    """拉取单条 story 并入库，返回是否新增"""
    async with sem:
        item = await _get_item(client, item_id)
        if not item or item.get("type") != "story":
            return False
        title = (item.get("title") or "").strip()
        url = item.get("url", "")
        if not title or not is_ai_related(title):
            return False
        pub_time = datetime.fromtimestamp(item["time"]) if item.get("time") else datetime.now()
        image, content = await _fetch_page_content(client, url)
        return await save_news(
            db,
            title=title,
            description="",
            content=content,
            image=image,
            author=item.get("by", ""),
            source_url=url,
            source_platform="hackernews",
            publish_time=pub_time,
            category_id=1,
        )


async def fetch_hn(db: AsyncSession) -> int:
    """采集 Hacker News 热门中的 AI 相关文章，并发拉取，返回新增条数"""
    count = 0
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            ids = await _get_top_ids(client)
            sem = asyncio.Semaphore(CONCURRENCY)
            tasks = [_process_item(client, db, item_id, sem) for item_id in ids]
            results = await asyncio.gather(*tasks, return_e