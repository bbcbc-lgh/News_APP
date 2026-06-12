"""
迁移 0002：新增新闻采集相关表和字段

变更内容：
  - news 表新增 source_platform、source_url、content_hash 字段
  - 新增 news_source 表（管理采集源配置）
  - 写入 4 条默认数据源记录
"""
import sqlalchemy as sa


async def upgrade(conn):
    # news 表新增字段
    await conn.execute(sa.text("""
        ALTER TABLE news
          ADD COLUMN source_platform VARCHAR(50) DEFAULT 'local' COMMENT '来源平台标识',
          ADD COLUMN source_url VARCHAR(500) COMMENT '原文链接',
          ADD COLUMN content_hash CHAR(32) COMMENT '标题MD5，用于去重';
    """))

    await conn.execute(sa.text("""
        ALTER TABLE news
          ADD UNIQUE KEY uk_content_hash (content_hash);
    """))

    # 新增 news_source 配置表
    await conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS news_source (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(50) NOT NULL COMMENT '显示名称',
            platform VARCHAR(50) NOT NULL COMMENT '平台标识',
            feed_url VARCHAR(500) NOT NULL COMMENT 'RSS或API地址',
            fetch_interval INT DEFAULT 120 COMMENT '采集间隔(分钟)',
            enabled TINYINT DEFAULT 1 COMMENT '是否启用',
            last_fetched_at DATETIME NULL COMMENT '最近采集时间',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        ) COMMENT='新闻采集源配置表';
    """))

    # 写入默认数据源
    await conn.execute(sa.text("""
        INSERT INTO news_source (name, platform, feed_url, fetch_interval, enabled) VALUES
        ('Hacker News',     'hackernews', 'https://hacker-news.firebaseio.com/v0', 60,  1),
        ('OpenAI Blog',     'openai',     'https://openai.com/blog/rss.xml',        120, 1),
        ('Google AI Blog',  'google_ai',  'https://blog.google/technology/ai/rss/', 120, 1),
        ('MIT Tech Review', 'mit',        'https://www.technologyreview.com/feed/', 120, 1);
    """))


async def downgrade(conn):
    await conn.execute(sa.text("DROP TABLE IF EXISTS news_source"))
    await conn.execute(sa.text("""
        ALTER TABLE news
          DROP INDEX uk_content_hash,
          DROP COLUMN source_platform,
          DROP COLUMN source_url,
          DROP COLUMN content_hash;
    """))
