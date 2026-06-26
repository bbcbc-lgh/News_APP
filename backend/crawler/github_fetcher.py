from datetime import datetime

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from crawler.base import save_news
from crawler.filters import is_ai_related
from crud.topic_tag import infer_and_tag
from utils.content_guard import markdown_to_excerpt


GITHUB_SEARCH = "https://api.github.com/search/repositories"
GITHUB_API = "https://api.github.com"
GITHUB_HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "NexusNews/1.0 (local personal news reader)",
}
QUERIES = [
    "topic:llm stars:>100",
    "topic:artificial-intelligence stars:>100",
    "topic:machine-learning stars:>100",
]
MAX_RESULTS_PER_QUERY = 3


def _parse_date(value: str | None) -> datetime:
    if not value:
        return datetime.now()
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        return datetime.now()


async def fetch_github_ai(db: AsyncSession) -> int:
    items = []
    seen = set()
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            for query in QUERIES:
                resp = await client.get(
                    GITHUB_SEARCH,
                    params={
                        "q": query,
                        "sort": "updated",
                        "order": "desc",
                        "per_page": str(MAX_RESULTS_PER_QUERY),
                    },
                    headers=GITHUB_HEADERS,
                )
                resp.raise_for_status()
                for repo in resp.json().get("items", []):
                    full_name = repo.get("full_name")
                    if full_name and full_name not in seen:
                        seen.add(full_name)
                        items.append(repo)
    except Exception as e:
        print(f"[github_ai] request failed: {e}")
        return 0

    count = 0
    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
        for repo in items:
            if await _save_repo(db, client, repo):
                count += 1

    print(f"[github_ai] inserted {count}")
    return count


async def _fetch_readme_excerpt(client: httpx.AsyncClient, full_name: str) -> str:
    try:
        resp = await client.get(
            f"{GITHUB_API}/repos/{full_name}/readme",
            headers={**GITHUB_HEADERS, "Accept": "application/vnd.github.raw+json"},
        )
        if resp.status_code == 404:
            return ""
        resp.raise_for_status()
        return markdown_to_excerpt(resp.text)
    except Exception:
        return ""


async def _save_repo(db: AsyncSession, client: httpx.AsyncClient, repo: dict) -> bool:
    full_name = repo.get("full_name") or ""
    description = repo.get("description") or ""
    if not full_name:
        return False
    if not is_ai_related(full_name, description):
        return False
    stars = int(repo.get("stargazers_count") or 0)
    forks = int(repo.get("forks_count") or 0)
    title = f"{full_name}: {description}" if description else full_name
    readme_excerpt = await _fetch_readme_excerpt(client, full_name)
    saved = await save_news(
        db,
        title=title,
        description=description,
        content=readme_excerpt,
        image=repo.get("owner", {}).get("avatar_url") or "",
        author=repo.get("owner", {}).get("login") or "GitHub",
        source_url=repo.get("html_url") or "",
        source_platform="github_ai",
        publish_time=_parse_date(repo.get("pushed_at") or repo.get("updated_at")),
        category_id=1,
        external_id=full_name,
        source_score=stars,
        source_comment_count=forks,
    )
    if saved:
        await infer_and_tag(db, saved, f"{title} {description} github open source llm")
        return True
    return False
