import re
import html as html_lib
from datetime import datetime
from email.utils import parsedate_to_datetime

import feedparser
import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from crawler.base import save_news
from crawler.filters import is_ai_related
from crud.topic_tag import infer_and_tag


RSS_FALLBACK_SOURCES = [
    {
        "platform": "openai",
        "name": "OpenAI News",
        "url": "https://openai.com/news/rss.xml",
        "category_id": 1,
        "requires_ai_filter": False,
    },
    {
        "platform": "google_ai",
        "name": "Google AI Blog",
        "url": "https://blog.google/technology/ai/rss/",
        "category_id": 1,
        "requires_ai_filter": False,
    },
    {
        "platform": "mit",
        "name": "MIT Tech Review",
        "url": "https://www.technologyreview.com/feed/",
        "category_id": 1,
        "requires_ai_filter": True,
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
    media = getattr(entry, "media_thumbnail", None)
    if media and isinstance(media, list):
        url = media[0].get("url", "")
        if url:
            return url

    for link in getattr(entry, "links", []):
        if link.get("type", "").startswith("image/"):
            url = link.get("href", "")
            if url:
                return url

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


def _clean_text(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html or "")
    text = html_lib.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _clean_summary(summary: str) -> str:
    text = _clean_text(summary)
    normalized = re.sub(r"[\s>：:。.!！-]+", "", text).lower()
    if normalized in {"点击查看原文", "查看原文", "阅读全文", "readmore", "continue reading"}:
        return ""
    return text


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


async def _load_rss_sources(db: AsyncSession) -> list[dict]:
    try:
        result = await db.execute(text("""
            SELECT name, platform, feed_url, source_group, trust_tier,
                   language, region, requires_ai_filter
            FROM news_source
            WHERE enabled = 1
              AND source_type = 'rss'
            ORDER BY trust_tier ASC, id ASC
        """))
        rows = result.mappings().all()
    except Exception as e:
        print(f"[rss] failed to load news_source, using fallback config: {e}")
        return RSS_FALLBACK_SOURCES

    sources = []
    for row in rows:
        sources.append({
            "platform": row["platform"],
            "name": row["name"],
            "url": row["feed_url"],
            "category_id": 1,
            "source_group": row.get("source_group"),
            "trust_tier": row.get("trust_tier"),
            "language": row.get("language"),
            "region": row.get("region"),
            "requires_ai_filter": bool(row.get("requires_ai_filter")),
        })
    return sources or RSS_FALLBACK_SOURCES


async def _mark_source_success(db: AsyncSession, platform: str):
    try:
        await db.execute(text("""
            UPDATE news_source
            SET last_fetched_at = NOW(), error_count = 0, last_error = NULL
            WHERE platform = :platform
        """), {"platform": platform})
        await db.commit()
    except Exception:
        await db.rollback()


async def _mark_source_error(db: AsyncSession, platform: str, message: str):
    try:
        await db.execute(text("""
            UPDATE news_source
            SET last_fetched_at = NOW(),
                error_count = error_count + 1,
                last_error = :message
            WHERE platform = :platform
        """), {"platform": platform, "message": message[:500]})
        await db.commit()
    except Exception:
        await db.rollback()


async def fetch_rss_source(db: AsyncSession, source: dict) -> int:
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
            resp = await client.get(source["url"], headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
            raw = resp.text
    except Exception as e:
        print(f"[{source['platform']}] request failed: {e}")
        await _mark_source_error(db, source["platform"], str(e))
        return 0

    feed = feedparser.parse(raw)
    count = 0
    for entry in feed.entries:
        title = entry.get("title", "").strip()
        if not title:
            continue
        description = _clean_summary(entry.get("summary", "").strip())
        if source.get("requires_ai_filter") and not is_ai_related(title, description):
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
            await infer_and_tag(db, saved, f"{title} {description}")
            count += 1
    await _mark_source_success(db, source["platform"])
    return count


async def fetch_all_rss(db: AsyncSession) -> dict:
    results = {}
    for source in await _load_rss_sources(db):
        n = await fetch_rss_source(db, source)
        results[source["platform"]] = n
        print(f"[{source['platform']}] inserted {n}")
    return results
