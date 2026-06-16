"""
迁移 0006：新增 search_history 用户搜索历史表
"""
import sqlalchemy as sa


async def upgrade(conn):
    await conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS search_history (
            id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
            user_id INT UNSIGNED NOT NULL,
            query VARCHAR(200) NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_user_time (user_id, created_at),
            FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
        ) COMMENT='用户搜索历史表';
    """))


async def downgrade(conn):
    await conn.execute(sa.text("DROP TABLE IF EXISTS search_history"))
