"""
迁移 0012：新增 vote 投票表，以及 news 表的 upvotes/downvotes 字段
"""
import sqlalchemy as sa


async def upgrade(conn):
    # 为 news 表增加 upvotes / downvotes 字段（如果不存在）
    for col, definition in [
        ("upvotes",   "INT UNSIGNED DEFAULT 0 COMMENT '点赞数'"),
        ("downvotes", "INT UNSIGNED DEFAULT 0 COMMENT '踩数'"),
    ]:
        exists = await conn.execute(sa.text("""
            SELECT COUNT(*) FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'news'
              AND COLUMN_NAME = :col
        """), {"col": col})
        if exists.scalar() == 0:
            await conn.execute(sa.text(
                f"ALTER TABLE news ADD COLUMN {col} {definition}"
            ))

    await conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS vote (
            user_id INT UNSIGNED NOT NULL,
            news_id INT UNSIGNED NOT NULL,
            value   TINYINT NOT NULL COMMENT '1=赞, -1=踩',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, news_id),
            FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
            FOREIGN KEY (news_id) REFERENCES news(id) ON DELETE CASCADE
        ) COMMENT='用户投票表';
    """))


async def downgrade(conn):
    await conn.execute(sa.text("DROP TABLE IF EXISTS vote"))
    # 不删除 news 上的字段（有数据时不安全）
