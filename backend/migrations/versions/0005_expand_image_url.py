"""
迁移 0005：扩展 news.image 字段长度 VARCHAR(255) → VARCHAR(500)

原因：CDN 图片 URL 经常超过 255 字符，超长会被静默截断导致图片 404。
"""
import sqlalchemy as sa


async def upgrade(conn):
    result = await conn.execute(sa.text(
        "SELECT CHARACTER_MAXIMUM_LENGTH FROM information_schema.COLUMNS "
        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'news' AND COLUMN_NAME = 'image'"
    ))
    row = result.fetchone()
    if row and row[0] < 500:
        await conn.execute(sa.text(
            "ALTER TABLE news MODIFY COLUMN image VARCHAR(500) COMMENT '封面图URL'"
        ))


async def downgrade(conn):
    await conn.execute(sa.text(
        "ALTER TABLE news MODIFY COLUMN image VARCHAR(255) COMMENT '封面图URL'"
    ))
