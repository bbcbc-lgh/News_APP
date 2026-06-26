"""
采集器基类，定义公共接口和入库逻辑
"""
import hashlib
import re
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from utils.content_guard import clean_content, clean_summary, clean_title
from utils.translator import translate_to_zh


def md5(s: str) -> str:
    return hashlib.md5(s.encode()).hexdigest()


def _normalize_title(title: str) -> str:
    text = title.lower().strip()
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"[\W_]+", "", text, flags=re.UNICODE)
    return text


async def save_news(db: AsyncSession, *, title: str, description: str = '',
                    content: str = '', image: str = '', author: str = '',
                    source_url: str = '', source_platform: str = '',
                    publish_time: datetime = None, category_id: int = 1,
                    external_id: str = '', source_score: int = 0,
                    source_comment_count: int = 0) -> bool:
    """
    将一条新闻写入数据库，通过 content_hash 去重。
    返回 True 表示新插入，False 表示已存在跳过。
    """
    title = clean_title(title)
    description = clean_summary(description)
    content = clean_content(content, min_chars=80) if content else ""
    if not title:
        return False

    # 优先用 URL 去重，URL 为空时 fallback 到标题
    hash_input = source_url.strip() if source_url and source_url.strip() else title
    hash_val = md5(hash_input)
    result = await db.execute(
        text("""
            SELECT id, description, content, description_zh, content_zh
            FROM news
            WHERE content_hash = :h
        """),
        {"h": hash_val}
    )
    existing = result.mappings().first()
    if existing:
        await _fill_missing_fields(db, existing, description, content)
        return False

    title_key = _normalize_title(title)
    if title_key:
        recent = await db.execute(text("""
            SELECT title
            FROM news
            WHERE publish_time >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            ORDER BY publish_time DESC
            LIMIT 500
        """))
        for (existing_title,) in recent.all():
            if _normalize_title(existing_title or "") == title_key:
                return False

    # 翻译（并发调用三个字段，失败不影响入库）
    title_zh, description_zh, content_zh = await _translate_fields(title, description, content)

    insert_result = await db.execute(text("""
        INSERT IGNORE INTO news
            (title, description, content, image, author,
             category_id, source_platform, source_url,
             external_id, content_hash, publish_time,
             source_score, source_comment_count,
             title_zh, description_zh, content_zh)
        VALUES
            (:title, :desc, :content, :image, :author,
             :cat_id, :platform, :url,
             :external_id, :hash, :pub_time,
             :source_score, :source_comment_count,
             :title_zh, :desc_zh, :content_zh)
    """), {
        "title": title[:200],
        "desc": description[:500] if description else '',
        "content": content,
        "image": image,
        "author": author[:100] if author else '',
        "cat_id": category_id,
        "platform": source_platform,
        "url": source_url[:500] if source_url else '',
        "external_id": external_id[:120] if external_id else None,
        "hash": hash_val,
        "pub_time": publish_time or datetime.now(),
        "source_score": source_score or 0,
        "source_comment_count": source_comment_count or 0,
        "title_zh": title_zh[:200] if title_zh else None,
        "desc_zh": description_zh[:500] if description_zh else None,
        "content_zh": content_zh or None,
    })
    await db.commit()
    if insert_result.rowcount > 0:
        # 返回新插入行的 id
        id_result = await db.execute(text("SELECT id FROM news WHERE content_hash = :h"), {"h": hash_val})
        row = id_result.fetchone()
        return row[0] if row else None
    return None


async def _fill_missing_fields(db: AsyncSession, row, description: str, content: str):
    updates = []
    params = {"id": row["id"]}

    if description and not row["description"]:
        updates.append("description = :description")
        params["description"] = description[:500]
        if not row["description_zh"]:
            desc_zh = await translate_to_zh(description, "description")
            if desc_zh:
                updates.append("description_zh = :description_zh")
                params["description_zh"] = desc_zh[:500]

    if content and not row["content"]:
        updates.append("content = :content")
        params["content"] = content
        if not row["content_zh"]:
            content_zh = await translate_to_zh(content, "content")
            if content_zh:
                updates.append("content_zh = :content_zh")
                params["content_zh"] = content_zh

    if updates:
        updates.append("updated_at = NOW()")
        await db.execute(text(f"UPDATE news SET {', '.join(updates)} WHERE id = :id"), params)
        await db.commit()


async def _translate_fields(title: str, description: str, content: str):
    """并发翻译标题、摘要、正文，任意失败返回空字符串。"""
    import asyncio
    results = await asyncio.gather(
        translate_to_zh(title, "title"),
        translate_to_zh(description, "description"),
        translate_to_zh(content, "content"),
        return_exceptions=True,
    )
    return tuple(r if isinstance(r, str) else "" for r in results)
