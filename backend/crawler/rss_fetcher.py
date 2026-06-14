"""
RSS 通用采集器，支持 OpenAI Blog、Google AI Blog、MIT Tech Review
"""
import re
import feedparser
import httpx
from datetime import datetime
from email.utils import parsedate_to_datetime
from sqlalchemy.ext.asyncio import AsyncSession
from crawler.base import save_news
from crawler.filters import is_ai_related


RSS_SOURCES = [
    {
        "platform": "openai",
        "name": "OpenAI Blog",
        "url": "https://openai.com/blog/rss.xml",
        "category_id": 1,
    },
    {
        "platform": "google_ai",
        "name": "Google AI Blog",
        "url": "https://blog.google/technology/ai/rss/",
        "category_id": 1,
    },
    {
        "platform": "mit",
        "name": "MIT Tech Review",
        "url": "https://www.technologyreview.com/feed/",
        "category_id": 1,
    },
]


def _parse_date(entry) -> datetime:
    for field in ("published", "updated"):
        val = getattr(entry, field, None)
        if val:
            try:
                return parsedate_to_datetime(val).replace(tzinfo=None)
            except Exception:
                pass
    return datetime.now()


def _get_image(entry) -> str:
    """从 RSS entry 提取封面图，依次尝试多个来源"""
    # media:thumbnail
    media = getattr(entry, "media_thumbnail", None)
    if media and isinstance(media, list):
        url = media[0].get("url", "")
        if url:
            return url
    # enclosure image
    for link in getattr(entry, "links", []):
        if link.get("type", "").startswith("image/"):
            url = link.get("href", "")
            if url:
                return url
    # 从 content 或 summary HTML 里提取第一张 <img>
    for field in ("content", "summary"):
        html = ""
        val = getattr(entry, field, None)
        if isinstance(val, list) and val:
            html = val[0].get("value", "")
        elif isinstance(val, str):
            html = val
        if html:
            m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', html, re.IGNORECASE)
            if m:
                url = m.group(1)
                if url.startswith("http"):
                    return url
    return ""


async def _get_og_image(client: httpx.AsyncClient, url: str) -> str:
    if not url:
        return ""
    try:
        resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"}, follow_redirects=True, timeout=8)
        html = resp.text[:120000]
    except Exception:
        return ""
    patterns = [
        r'<meta[^>]+property=["\']og:image(?::secure_url)?["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image(?::secure_url)?["\']',
        r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']twitter:image["\']',
    ]
    for pattern in patterns:
        m = re.search(pattern, html, re.IGNORECASE)
        if m:
            image = m.group(1).strip()
            if image.startswith("http"):
                return image
    return ""


async def fetch_rss_source(db: AsyncSession, source: dict) -> int:
    """采集单个 RSS 源，返回新增条数"""
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
            resp = await client.get(source["url"], headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
            raw = resp.text
    except Exception as e:
        print(f"[{source['platform']}] 请求失败: {e}")
        return 0

    feed = feedparser.parse(raw)
    count = 0
    for entry in feed.entries:
        title = entry.get("title", "").strip()
        if not title:
            continue
        description = entry.get("summary", "").strip()
        # MIT 是综合科技媒体，需过滤 AI 相关
        if source["platform"] == "mit" and not is_ai_related(title, description):
            continue
        source_url = entry.get("link", "")
        image = _get_image(entry)
        if not image:
            image = await _get_og_image(client, source_url)
        saved = await save_news(
            db,
            title=title,
            description=description,
            content=entry.get("content", [{}])[0].get("value", "") if entry.get("content") else "",
            image=image,
            author=entry.get("author", source["name"]),
            source_url=source_url,
            source_platform=source["platform"],
            publish_time=_parse_date(entry),
            category_id=source["category_id"],
        )
        if saved:
            count += 1
    return count


async def fetch_all_rss(db: AsyncSession) -> dict:
    """采集全部 RSS 源，返回各平台新增数量"""
    results = {}
    for source in RSS_SOURCES:
        n = await fetch_rss_source(db, source)
        results[source["platform"]] = n
        print(f"[{source['platform']}] 新增 {n} 条")
    return results
