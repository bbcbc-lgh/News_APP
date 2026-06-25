"""
使用 Claude Haiku 翻译英文新闻内容为中文。
base_url 已含 /v1，需去除后再传给 SDK，由 SDK 统一拼接。
"""
import html
import re

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

_REFUSAL_PATTERNS = (
    "i can't discuss that",
    "i can’t discuss that",
    "i can't help",
    "i can’t help",
    "i'm ready to help",
    "i'm sorry",
    "i am sorry",
    "i appreciate you sharing",
    "i need to be straightforward",
    "could you paste",
    "could you share",
    "provided only contains",
    "copyrighted",
    "full article from a blog",
    "translate the complete text",
    "word-for-word",
    "not a news article",
    "我注意到你提供的内容",
    "请确认你是否想让我翻译",
    "不是新闻文章",
    "我准备好了",
    "没有看到需要翻译",
    "请提供你想翻译",
    "我无法完整翻译",
    "不能直接翻译",
    "受版权保护",
    "无法协助",
    "不能讨论",
    "无法讨论",
)

_PREFACE_PATTERNS = (
    r"^这是一篇[^。\n]{0,60}。我为您翻译如下[:：]\s*",
    r"^这是一篇[^。\n]{0,60}的翻译[:：]\s*",
    r"^我为您翻译如下[:：]\s*",
    r"^以下是(?:这篇|该)?[^。\n]{0,40}的?中文翻译[:：]\s*",
    r"^翻译如下[:：]\s*",
)


def _plain_text(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _meaningful_length(text: str) -> int:
    return len(re.findall(r"[\w\u4e00-\u9fff]", _plain_text(text), flags=re.UNICODE))


def _is_mostly_chinese(text: str) -> bool:
    plain = _plain_text(text)
    cjk_count = len(re.findall(r"[\u4e00-\u9fff]", plain))
    latin_count = len(re.findall(r"[a-zA-Z]", plain))
    return cjk_count >= 4 and cjk_count >= latin_count


def _strip_model_preface(text: str) -> str:
    cleaned = text.strip()
    for pattern in _PREFACE_PATTERNS:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


def _is_bad_translation(text: str, field: str) -> bool:
    normalized = re.sub(r"\s+", " ", text).strip().lower()
    if not normalized:
        return True
    if any(pattern in normalized for pattern in _REFUSAL_PATTERNS):
        return True
    return field == "title" and ("\n" in text or len(text) > 120)


async def translate_to_zh(text: str, field: str = "content") -> str:
    """将英文文本翻译成中文，失败时返回空字符串。"""
    if not text or not text.strip():
        return ""
    clean_text = _plain_text(text)
    if not clean_text or _is_mostly_chinese(clean_text):
        return ""
    if field in {"title", "description"} and _meaningful_length(clean_text) < 18:
        return ""
    if field == "content" and _meaningful_length(clean_text) > 1200:
        return ""
    if not _API_KEY:
        return ""

    hint = {
        "title": "这是一条 AI/科技新闻标题，请翻译成简洁的中文标题，不要加任何解释。",
        "description": "这是一条新闻摘要，请翻译成流畅的中文，保留原意，不要加任何解释。",
        "content": "这是一篇新闻正文，请翻译成流畅的中文，保留段落结构，不要加任何解释。",
    }.get(field, "请将以下内容翻译成中文，不要加任何解释。")

    prompt = f"{hint}\n\n{clean_text[:3000]}"

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
            translated = _strip_model_preface(r.json()["content"][0]["text"].strip())
            return "" if _is_bad_translation(translated, field) else translated
    except Exception as e:
        print(f"[translator] 翻译失败 ({field}): {e}")
        return ""
