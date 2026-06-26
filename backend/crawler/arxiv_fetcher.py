from datetime import datetime
from time import mktime
from urllib.parse import urlencode

import feedparser
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from crawler.base import save_news
from crud.topic_tag import infer_and_tag
from utils.content_guard import clean_content, clean_summary


ARXIV_API = "https://export.arxiv.org/api/query"
ARXIV_QUERY = "cat:cs.AI OR cat:cs.LG OR cat:cs.CL"
MAX_RESULTS = 10


def _entry_id(entry) -> str:
    raw = entry.get("id", "") or entry.get("link", "")
    return raw.rsplit("/", 1)[-1].strip()


def _entry_date(entry) -> datetime:
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if parsed:
        return datetime.fromtimestamp(mktime(parsed))
    return datetime.now()


def _entry_authors(entry) -> str:
    authors = entry.get("authors") or []
    names = [a.get("name", "").strip() for a in authors if a.get("name")]
    return ", ".join(names[:3])


async def fetch_arxiv(db: AsyncSession) -> int:
    params = urlencode({
        "search_query": ARXIV_QUERY,
        "start": 0,
        "max_results": MAX_RESULTS,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    })
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            resp = await client.get(
                f"{ARXIV_API}?{params}",
                headers={"User-Agent": "NexusNews/1.0 (local personal news reader)"},
            )
            resp.raise_for_status()
    except Exception as e:
        print(f"[arxiv_ai] request failed: {e}")
        return 0

    feed = feedparser.parse(resp.text)
    count = 0
    for entry in feed.entries:
        title = " ".join((entry.get("title") or "").split())
        summary_raw = " ".join((entry.get("summary") or "").split())
        summary = clean_summary(summary_raw)
        content = clean_content(summary_raw, min_chars=120, max_chars=2500)
        arxiv_id = _entry_id(entry)
        source_url = entry.get("link") or f"https://arxiv.org/abs/{arxiv_id}"
        if not title or not arxiv_id:
            continue

        saved = await save_news(
            db,
            title=title,
            description=summary,
            content=content,
            image="",
            author=_entry_authors(entry) or "arXiv",
            source_url=source_url,
            source_platform="arxiv_ai",
            publish_time=_entry_date(entry),
            category_id=1,
            external_id=arxiv_id,
        )
        if saved:
            await infer_and_tag(db, saved, f"{title} {summary} paper arxiv research")
            count += 1

    print(f"[arxiv_ai] inserted {count}")
    return count
