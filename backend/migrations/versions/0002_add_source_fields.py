"""
迁移 0002：news 表新增 source_platform、source_url、content_hash 字段
"""
import sqlalchemy as sa

async def upgrade(conn):
    await conn.execute(sa.text("""
        ALTER TABLE news
        ADD COLUMN IF NOT EXISTS source_platform VARCHAR(50) COMMENT '数据源平台标识',
        ADD COLUMN IF NOT EXISTS source_url VARCHAR(500) COMMENT '原文链接',
        ADD COLUMN IF NOT EXISTS content_hash VARCHAR(32) COMMENT '内容哈希去重'
    """))
    await conn.execute(sa.text("""
        CREATE INDEX IF NOT EXISTS idx_source_platform ON news (source_platform)
    """))

async def downgrade(conn):
    await conn.execute(sa.text("ALTER TABLE news DROP COLUMN IF EXISTS source_platform"))
    await conn.execute(sa.text("ALTER TABLE news DROP COLUMN IF EXISTS source_url"))
    await conn.execute(sa.text("ALTER TABLE news DROP COLUMN IF EXISTS content_hash"))
