"""
迁移 0002：news 表新增 source_platform、source_url、content_hash 字段
"""
import sqlalchemy as sa

async def upgrade(conn):
    # 逐列检查是否存在，不存在才添加（兼容 MySQL 不支持 ADD COLUMN IF NOT EXISTS）
    result = await conn.execute(sa.text(
        "SELECT COUNT(*) FROM information_schema.COLUMNS "
        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'news' AND COLUMN_NAME = 'source_platform'"
    ))
    if result.scalar() == 0:
        await conn.execute(sa.text(
            "ALTER TABLE news ADD COLUMN source_platform VARCHAR(50) COMMENT 'data source platform'"
        ))

    result = await conn.execute(sa.text(
        "SELECT COUNT(*) FROM information_schema.COLUMNS "
        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'news' AND COLUMN_NAME = 'source_url'"
    ))
    if result.scalar() == 0:
        await conn.execute(sa.text(
            "ALTER TABLE news ADD COLUMN source_url VARCHAR(500) COMMENT 'original article url'"
        ))

    result = await conn.execute(sa.text(
        "SELECT COUNT(*) FROM information_schema.COLUMNS "
        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'news' AND COLUMN_NAME = 'content_hash'"
    ))
    if result.scalar() == 0:
        await conn.execute(sa.text(
            "ALTER TABLE news ADD COLUMN content_hash VARCHAR(32) COMMENT 'dedup hash'"
        ))

    # 加索引（忽略已存在错误）
    try:
        await conn.execute(sa.text(
            "CREATE INDEX idx_source_platform ON news (source_platform)"
        ))
    except Exception:
        pass

async def downgrade(conn):
    for col in ("source_platform", "source_url", "content_hash"):
        try:
            await conn.execute(sa.text(f"ALTER TABLE news DROP COLUMN {col}"))
        except Exception:
            pass
