"""
迁移 0011：新增 reading_progress 阅读进度表
"""
import sqlalchemy as sa


async def upgrade(conn):
    await conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS reading_progress (
            user_id INT UNSIGNED NOT NULL,
            news_id INT UNSIGNED NOT NULL,
            progress INT DEFAULT 0 COMMENT '阅读进度百分比 0-100',
            last_position INT DEFAULT 0 COMMENT '最后阅读的像素位置',
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, news_id),
            FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
            FOREIGN KEY (news_id) REFERENCES news(id) ON DELETE CASCADE
        ) COMMENT='用户阅读进度表';
    """))


async def downgrade(conn):
    await conn.execute(sa.text("DROP TABLE IF EXISTS reading_progress"))
