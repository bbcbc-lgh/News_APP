"""
Add external source metrics for community/research feeds.
"""
import sqlalchemy as sa


async def _column_exists(conn, table: str, column: str) -> bool:
    result = await conn.execute(sa.text("""
        SELECT COUNT(*)
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = :table
          AND COLUMN_NAME = :column
    """), {"table": table, "column": column})
    return result.scalar() > 0


async def _add_column(conn, table: str, column: str, ddl: str):
    if not await _column_exists(conn, table, column):
        await conn.execute(sa.text(f"ALTER TABLE `{table}` ADD COLUMN {ddl}"))


async def upgrade(conn):
    await _add_column(conn, "news", "external_id", "external_id VARCHAR(120) NULL COMMENT 'source item id'")
    await _add_column(conn, "news", "source_score", "source_score INT NOT NULL DEFAULT 0 COMMENT 'source-native score'")
    await _add_column(conn, "news", "source_comment_count", "source_comment_count INT NOT NULL DEFAULT 0 COMMENT 'source-native comments'")

    result = await conn.execute(sa.text("""
        SELECT COUNT(*)
        FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'news'
          AND INDEX_NAME = 'idx_source_external_id'
    """))
    if result.scalar() == 0:
        await conn.execute(sa.text("CREATE INDEX idx_source_external_id ON news (source_platform, external_id)"))

    await conn.execute(sa.text("""
        INSERT INTO news_source
            (name, platform, feed_url, source_type, source_group, trust_tier,
             language, region, fetch_interval, enabled, requires_ai_filter)
        VALUES
            ('arXiv AI', 'arxiv_ai', 'https://export.arxiv.org/api/query', 'arxiv', 'research', 1, 'en', 'global', 240, 1, 0)
        ON DUPLICATE KEY UPDATE
            name = VALUES(name),
            feed_url = VALUES(feed_url),
            source_type = VALUES(source_type),
            source_group = VALUES(source_group),
            trust_tier = VALUES(trust_tier),
            language = VALUES(language),
            region = VALUES(region),
            fetch_interval = VALUES(fetch_interval),
            enabled = VALUES(enabled),
            requires_ai_filter = VALUES(requires_ai_filter)
    """))


async def downgrade(conn):
    for column in ("source_comment_count", "source_score", "external_id"):
        if await _column_exists(conn, "news", column):
            await conn.execute(sa.text(f"ALTER TABLE news DROP COLUMN {column}"))
