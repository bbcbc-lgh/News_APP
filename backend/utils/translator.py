"""
使用 Claude Haiku 翻译英文新闻内容为中文。
base_url 已含 /v1，需去除后再传给 SDK，由 SDK 统一拼接。
"""
import httpx
from config.env import get

_API_KEY = get("ANTHROPIC_API_KEY")
_BASE_URL = get("ANTHROPIC_BASE_URL", "").rstrip("/")
# 代理 base_url 含 /v1，去掉让 SDK 自己加；若不含则保持原样
if _BASE_URL.endswith("/v1"):
    _BASE_URL = _BASE_URL[:-3]

_MODEL = "claude-haiku-4-5-20251001"
_HEADERS = {
    "x-api-key": _API_KEY,
    "anthropic-version": "2023-06-01",
    "content-type": "application/json",
}


async def translate_to_zh(text: str, field: str = "content") -> str:
    """将英文文本翻译成中文，失败时返回空字符串。"""
    if not text or not text.strip():
        return ""
    if not _API_KEY:
        return ""

    hint = {
        "title": "这是一条 AI/科技新闻标题，请翻译成简洁的中文标题，不要加任何解释。",
        "description": "这是一条新闻摘要，请翻译成流畅的中文，保留原意，不要加任何解释。",
        "content": "这是一篇新闻正文，请翻译成流畅的中文，保留段落结构，不要加任何解释。",
    }.get(field, "请将以下内容翻译成中文，不要加任何解释。")

    prompt = f"{hint}\n\n{text[:3000]}"

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                f"{_BASE_URL}/v1/messages",
                headers=_HEADERS,
                json={
                    "model": _MODEL,
                    "max_tokens": 1024,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            r.raise_for_status()
            return r.json()["content"][0]["text"].strip()
    except Exception as e:
        print(f"[translator] 翻译失败 ({field}): {e}")
        return ""
