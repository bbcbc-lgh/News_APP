"""
迁移 0001：初始建表

包含项目所有初始表结构：
  - category（新闻分类）
  - news（新闻）
  - user（用户）
  - user_token（用户令牌）
  - favorite（收藏）
  - history（浏览历史）
"""
import sqlalchemy as sa


async def upgrade(conn):
    """建立全部初始表"""
    await conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS category (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(50) NOT NULL COMMENT '分类名称',
            sort_order INT DEFAULT 0 COMMENT '排序值，越小越靠前',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) COMMENT='新闻分类表';
    """))

    await conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS news (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(200) NOT NULL COMMENT '新闻标题',
            content TEXT COMMENT '正文内容',
            description VARCHAR(500) COMMENT '摘要',
            image VARCHAR(255) COMMENT '封面图URL',
            author VARCHAR(100) COMMENT '作者',
            category_id INT NOT NULL COMMENT '所属分类ID',
            views INT DEFAULT 0 COMMENT '浏览量',
            publish_time DATETIME COMMENT '发布时间',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_category (category_id),
            INDEX idx_publish_time (publish_time)
        ) COMMENT='新闻表';
    """))

    await conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS user (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
            password VARCHAR(255) NOT NULL COMMENT '密码哈希',
            nickname VARCHAR(50) COMMENT '昵称',
            avatar VARCHAR(255) DEFAULT 'https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg' COMMENT '头像URL',
            gender VARCHAR(10) DEFAULT 'unknown' COMMENT '性别: male/female/unknown',
            bio VARCHAR(200) DEFAULT '这个人很懒，什么都没留下' COMMENT '个人简介',
            phone VARCHAR(20) COMMENT '手机号',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) COMMENT='用户表';
    """))

    await conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS user_token (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            token VARCHAR(255) NOT NULL UNIQUE COMMENT '访问令牌',
            expires_at DATETIME NOT NULL COMMENT '过期时间',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_token (token),
            FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
        ) COMMENT='用户令牌表';
    """))

    await conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS favorite (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            news_id INT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY uq_user_news (user_id, news_id),
            FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
        ) COMMENT='用户收藏表';
    """))

    await conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS history (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            news_id INT NOT NULL,
            view_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '浏览时间',
            FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
            INDEX idx_user_view (user_id, view_time)
        ) COMMENT='用户浏览历史表';
    """))


async def downgrade(conn):
    """删除全部初始表（谨慎操作，将丢失所有数据）"""
    for table in ("history", "favorite", "user_token", "user", "news", "category"):
        await conn.execute(sa.text(f"DROP TABLE IF EXISTS {table}"))
