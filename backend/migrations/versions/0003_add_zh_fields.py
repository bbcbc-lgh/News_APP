"""
迁移 0003：news 表新增 title_zh、description_zh、content_zh 翻译字段
"""
import sqlalchemy as sa


async def upgrade(conn):
    for col, ddl in [
        ("title_zh",       "ALTER TABLE news ADD COLUMN title_zh VARCHAR(500) DEFAULT NULL COMMENT '中文标题'"),
        ("description_zh", "ALTER TABLE news ADD COLUMN description_zh TEXT DEFAULT NULL COMMENT '中文摘要'"),
        ("content_zh",     "ALTER TABLE news ADD COLUMN content_zh LONGTEXT DEFAULT NULL COMMENT '中文正文'"),
    ]:
        result = await conn.execute(sa.text(
            "SELECT COUNT(*) FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'news' AND COLUMN_NAME = :col"
        ), {"col": col})
        if result.scalar() == 0:
            await conn.execute(sa.text(ddl))
            print(f"  added column: {col}")
        else:
            print(f"  skip (exists): {col}")


async def downgrade(conn):
    for col in ("title_zh", "description_zh", "content_zh"):
        try:
            await conn.execute(sa.text(f"ALTER TABLE news DROP COLUMN {col}"))
        except Exception:
            pass
