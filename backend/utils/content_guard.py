import html
import re


BAD_TEXT_MARKERS = (
    "i appreciate you sharing",
    "i need to be straightforward",
    "i can't translate",
    "i cannot translate",
    "copyrighted",
    "word-for-word",
    "full article from a blog",
    "please provide the text",
    "could you paste",
    "我准备好了",
    "没有看到需要翻译",
    "请提供你想翻译",
    "我无法完整翻译",
    "不能直接翻译",
    "受版权保护",
    "我注意到你提供的内容",
)

READ_MORE_TEXT = {
    "点击查看原文",
    "查看原文",
    "阅读全文",
    "继续阅读",
    "readmore",
    "continuereading",
}


def _compact(text: str) -> str:
    return re.sub(r"[\s>：:。.!！?？-]+", "", text).lower()


def strip_html(raw: str) -> str:
    if not raw:
        return ""
    text = re.sub(r"<(script|style|noscript|svg|nav|header|footer|aside|form|button)[^>]*>[\s\S]*?</\1>", " ", raw, flags=re.IGNORECASE)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</(p|div|section|article|h[1-6]|li|blockquote|pre)>", "\n\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<li[^>]*>", "\n- ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n\s+", "\n", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def is_bad_text(raw: str) -> bool:
    text = strip_html(raw)
    if not text:
        return True
    if _compact(text) in READ_MORE_TEXT:
        return True
    lower = text.lower()
    return any(marker in lower for marker in BAD_TEXT_MARKERS)


def clean_title(raw: str) -> str:
    text = strip_html(raw)
    return "" if is_bad_text(text) else re.sub(r"\s+", " ", text).strip()


def clean_summary(raw: str, max_chars: int = 500) -> str:
    text = strip_html(raw)
    if is_bad_text(text):
        return ""
    return re.sub(r"\s+", " ", text).strip()[:max_chars]


def clean_content(raw: str, *, min_chars: int = 120, max_chars: int = 6000) -> str:
    text = strip_html(raw)
    if is_bad_text(text):
        return ""
    meaningful = len(re.findall(r"[\w\u4e00-\u9fff]", text, flags=re.UNICODE))
    if meaningful < min_chars:
        return ""
    if len(text) <= max_chars:
        return text
    clipped = text[:max_chars]
    boundary = max(clipped.rfind("\n\n"), clipped.rfind("。"), clipped.rfind(". "))
    if boundary > max_chars * 0.55:
        clipped = clipped[:boundary + 1]
    return clipped.strip()


def markdown_to_excerpt(raw: str, *, max_chars: int = 1400) -> str:
    if not raw:
        return ""
    text = re.sub(r"```[\s\S]*?```", " ", raw)
    text = re.sub(r"<!--[\s\S]*?-->", " ", text)
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            if lines and lines[-1] != "":
                lines.append("")
            continue
        if line.endswith("|") or line.count("|") >= 3:
            continue
        if line.startswith(("![", "[![")) or "shields.io" in line or "badge" in line.lower():
            continue
        line = re.sub(r"!\[[^\]]*]\([^)]*\)", " ", line)
        line = re.sub(r"\[([^\]]+)]\([^)]*\)", r"\1", line)
        line = re.sub(r"`([^`]+)`", r"\1", line)
        line = re.sub(r"^[#>*\-\d.\s]+", "", line)
        line = re.sub(r"[*_~]{1,3}", "", line).strip()
        if line:
            lines.append(line)
    return clean_content("\n".join(lines), min_chars=160, max_chars=max_chars)
