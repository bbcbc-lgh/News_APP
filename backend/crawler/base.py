"""
采集器基类，定义公共接口和入库逻辑
"""
import hashlib
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text


def md5(s: str) -> str:
    return hashlib.md5(s.encode()).hexdigest()


async def save_news(db: AsyncSession, *, title: str, description: str = '',
                    content: str = '', image: str = '', author: str = '',
                    source_url: str = '', source_platform: str = '',
                    publish_time: datetime = None, category_id: int = 1) -> bool:
    """
    将一条新闻写入数据库，通过 content_hash 去重。
    返回 True 表示新插入，False 表示已存在跳过。
    """
    hash_val = md5(title)
    result = await db.execute(
        text("SELECT id FROM news WHERE content_hash = :h"),
        {"h": hash_val}
    )
    if result.fetchone():
        return False

    await db.execute(text("""
        INSERT INTO news
            (title, description, content, image, author,
             category_id, source_platform, source_url,
             content_hash, publish_time)
        VALUES
            (:title, :desc, :content, :image, :author,
             :cat_id, :platform, :url,
             :hash, :pub_time)
    """), {
        "title": title[:200],
        "desc": description[:500] if description else '',
        "content": content,
        "image": image,
        "author": author[:100] if author else '',
        "cat_id": category_id,
        "platform": source_platform,
        "url": source_url[:500] if source_url else '',
        "hash": hash_val,
        "pub_time": publish_time or datetime.now(),
    })
    await db.commit()
    return True
