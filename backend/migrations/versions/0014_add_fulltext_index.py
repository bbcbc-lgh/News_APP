"""
迁移 0014：给 news 表添加全文索引（ngram parser，支持中文）
"""
import sqlalchemy as sa


async def upgrade(conn):
    # 检查索引是否已存在
    exists = await conn.execute(sa.text("""
        SELECT COUNT(*) FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'news'
          AND INDEX_NAME = 'ft_news_search'
    """))
    if exists.scalar() == 0:
        # WITH PARSER ngram 支持中文分词（MySQL 5.7.6+）
        await conn.execute(sa.text("""
            ALTER TABLE news
            ADD FULLTEXT INDEX ft_news_search (title, title_zh, description, description_zh)
            WITH PARSER ngram
        """))


async def downgrade(conn):
    await conn.execute(sa.text("ALTER TABLE news DROP INDEX ft_news_search"))
