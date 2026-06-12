-- AI 掘金头条 — 数据库初始化脚本
-- 执行方式：mysql -u root -p < data.sql
-- 说明：建表后通过迁移脚本 python migrations/migrate.py 完成字段扩展，
--       新闻数据由 Celery 采集器自动抓取，无需手动导入。

CREATE DATABASE IF NOT EXISTS my_first_app DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE my_first_app;

-- ───────────────────────────────────────────
-- 用户表
-- ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `user` (
  `id`         INT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '用户ID',
  `username`   VARCHAR(50)  NOT NULL COMMENT '用户名',
  `password`   VARCHAR(255) NOT NULL COMMENT '密码（bcrypt）',
  `nickname`   VARCHAR(50)  NULL DEFAULT NULL COMMENT '昵称',
  `avatar`     VARCHAR(255) NULL DEFAULT NULL COMMENT '头像URL',
  `gender`     ENUM('male','female','unknown') NULL DEFAULT 'unknown' COMMENT '性别',
  `bio`        VARCHAR(500) NULL DEFAULT NULL COMMENT '个人简介',
  `phone`      VARCHAR(20)  NULL DEFAULT NULL COMMENT '手机号',
  `created_at` TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `username_UNIQUE` (`username`),
  UNIQUE INDEX `phone_UNIQUE` (`phone`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户信息表';

-- ───────────────────────────────────────────
-- 用户令牌表
-- ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `user_token` (
  `id`         INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id`    INT UNSIGNED NOT NULL,
  `token`      VARCHAR(255) NOT NULL,
  `expires_at` TIMESTAMP    NOT NULL,
  `created_at` TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `token_UNIQUE` (`token`),
  INDEX `fk_user_token_user_idx` (`user_id`),
  CONSTRAINT `fk_user_token_user`
    FOREIGN KEY (`user_id`) REFERENCES `user` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户令牌表';

-- ───────────────────────────────────────────
-- 新闻分类表
-- ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `news_category` (
  `id`         INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `name`       VARCHAR(50)  NOT NULL,
  `sort_order` INT          NOT NULL DEFAULT 0,
  `created_at` TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `name_UNIQUE` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='新闻分类表';

-- ───────────────────────────────────────────
-- 新闻表（含采集器扩展字段）
-- ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `news` (
  `id`              INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `title`           VARCHAR(255) NOT NULL,
  `description`     VARCHAR(500) NULL DEFAULT NULL,
  `content`         TEXT         NOT NULL,
  `image`           VARCHAR(255) NULL DEFAULT NULL,
  `author`          VARCHAR(50)  NULL DEFAULT NULL,
  `category_id`     INT UNSIGNED NOT NULL,
  `views`           INT UNSIGNED NOT NULL DEFAULT 0,
  `publish_time`    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_at`      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `source_platform` VARCHAR(50)  NULL DEFAULT 'local' COMMENT '来源平台',
  `source_url`      VARCHAR(500) NULL DEFAULT NULL COMMENT '原文链接',
  `content_hash`    CHAR(32)     NULL DEFAULT NULL COMMENT 'MD5去重',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_content_hash` (`content_hash`),
  INDEX `fk_news_category_idx` (`category_id`),
  INDEX `idx_publish_time` (`publish_time` DESC),
  CONSTRAINT `fk_news_category`
    FOREIGN KEY (`category_id`) REFERENCES `news_category` (`id`)
    ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='新闻表';

-- ───────────────────────────────────────────
-- 相关新闻关联表
-- ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `related_news` (
  `id`             INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `news_id`        INT UNSIGNED NOT NULL,
  `related_news_id` INT UNSIGNED NOT NULL,
  `created_at`     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `news_related_unique` (`news_id`, `related_news_id`),
  CONSTRAINT `fk_related_news_news`
    FOREIGN KEY (`news_id`) REFERENCES `news` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_related_news_related`
    FOREIGN KEY (`related_news_id`) REFERENCES `news` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='相关新闻关联表';

-- ───────────────────────────────────────────
-- 收藏表
-- ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `favorite` (
  `id`         INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id`    INT UNSIGNED NOT NULL,
  `news_id`    INT UNSIGNED NOT NULL,
  `created_at` TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE INDEX `user_news_unique` (`user_id`, `news_id`),
  CONSTRAINT `fk_favorite_user`
    FOREIGN KEY (`user_id`) REFERENCES `user` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_favorite_news`
    FOREIGN KEY (`news_id`) REFERENCES `news` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='收藏表';

-- ───────────────────────────────────────────
-- 浏览历史表
-- ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `history` (
  `id`        INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id`   INT UNSIGNED NOT NULL,
  `news_id`   INT UNSIGNED NOT NULL,
  `view_time` TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  INDEX `idx_view_time` (`view_time` DESC),
  CONSTRAINT `fk_history_user`
    FOREIGN KEY (`user_id`) REFERENCES `user` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_history_news`
    FOREIGN KEY (`news_id`) REFERENCES `news` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='浏览历史表';

-- ───────────────────────────────────────────
-- AI 聊天记录表
-- ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `ai_chat` (
  `id`         INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id`    INT UNSIGNED NOT NULL,
  `message`    TEXT         NOT NULL,
  `response`   TEXT         NOT NULL,
  `created_at` TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  INDEX `idx_created_at` (`created_at` DESC),
  CONSTRAINT `fk_ai_chat_user`
    FOREIGN KEY (`user_id`) REFERENCES `user` (`id`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AI聊天记录表';

-- ───────────────────────────────────────────
-- 新闻来源配置表（采集器使用）
-- ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `news_source` (
  `id`          INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `name`        VARCHAR(100) NOT NULL COMMENT '来源名称',
  `platform`    VARCHAR(50)  NOT NULL COMMENT '平台标识',
  `url`         VARCHAR(500) NOT NULL COMMENT '采集地址',
  `source_type` VARCHAR(20)  NOT NULL DEFAULT 'rss' COMMENT 'rss/api',
  `is_active`   TINYINT(1)   NOT NULL DEFAULT 1,
  `created_at`  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_platform` (`platform`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='新闻来源配置表';

-- ───────────────────────────────────────────
-- schema_migrations（迁移版本记录）
-- ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS `schema_migrations` (
  `version`    VARCHAR(50)  NOT NULL,
  `applied_at` TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`version`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='数据库迁移版本记录';

-- ───────────────────────────────────────────
-- 初始化数据
-- ───────────────────────────────────────────

-- 新闻分类（AI 技术相关）
INSERT INTO `news_category` (`name`, `sort_order`) VALUES
('头条',   1),
('社会',   2),
('国内',   3),
('国际',   4),
('娱乐',   5),
('体育',   6),
('科技',   7),
('财经',   8);

-- 新闻来源（采集器默认配置）
INSERT INTO `news_source` (`name`, `platform`, `url`, `source_type`) VALUES
('Hacker News',       'hackernews', 'https://hacker-news.firebaseio.com/v0', 'api'),
('OpenAI Blog',       'openai',     'https://openai.com/blog/rss.xml',       'rss'),
('Google AI Blog',    'google_ai',  'https://blog.google/technology/ai/rss/', 'rss'),
('MIT Tech Review',   'mit',        'https://www.technologyreview.com/feed/', 'rss');

-- 迁移版本标记（与 migrations/ 目录对齐）
INSERT IGNORE INTO `schema_migrations` (`version`) VALUES ('0001'), ('0002');
