"""
迁移 0009：新增 reading_behavior 用户阅读行为表
"""
import sqlalchemy as sa


async def upgrade(conn):
    await conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS reading_behavior (
            id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
            user_id INT UNSIGNED NOT NULL,
            news_id INT UNSIGNED NOT NULL,
            action_type VARCHAR(20) NOT NULL COMMENT 'view/favorite/share/complete',
            duration INT DEFAULT 0 COMMENT '阅读时长(秒)',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_user_time (user_id, created_at),
            INDEX idx_news (news_id),
            FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
            FOREIGN KEY (news_id) REFERENCES news(id) ON DELETE CASCADE
        ) COMMENT='用户阅读行为日志表';
    """))


async def downgrade(conn):
    await conn.execute(sa.text("DROP TABLE IF EXISTS reading_behavior"))
