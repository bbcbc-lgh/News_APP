"""
采集器基类，定义公共接口和入库逻辑
"""
import hashlib
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from utils.translator import translate_to_zh


def md5(s: str) -> str:
    return hashlib.md5(s.encode()).hexdigest()


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
    # 优先用 URL 去重，URL 为空时 fallback 到标题
    hash_input = source_url.strip() if source_url and source_url.strip() else title
    hash_val = md5(hash_input)
    result = await db.execute(
        text("SELECT id FROM news WHERE content_hash = :h"),
        {"h": hash_val}
    )
    if result.fetchone():
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
