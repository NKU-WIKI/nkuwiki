-- 创建用户和数据库前切换到postgres数据库
\c postgres;
CREATE USER nkuwiki_user WITH PASSWORD '123456' CREATEDB CREATEROLE;
CREATE DATABASE nkuwiki_db OWNER nkuwiki_user;
\c nkuwiki_db;

-- 授予模式权限
GRANT CREATE, USAGE ON SCHEMA nkuwiki TO nkuwiki_user;

-- 添加超级用户权限（临时）
ALTER USER nkuwiki_user WITH SUPERUSER;

-- 删除所有冗余操作
\echo '开始执行初始化脚本'
SET search_path TO nkuwiki;

-- 创建模式并授权
CREATE SCHEMA IF NOT EXISTS nkuwiki AUTHORIZATION nkuwiki_user;
GRANT USAGE ON SCHEMA nkuwiki TO nkuwiki_user;
GRANT CREATE ON SCHEMA nkuwiki TO nkuwiki_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA nkuwiki TO nkuwiki_user;
GRANT USAGE, CREATE ON SCHEMA public TO nkuwiki_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA nkuwiki GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO nkuwiki_user;

-- 删除所有旧表和相关对象
DROP TABLE IF EXISTS nkuwiki.wechat_articles CASCADE;

-- 创建新的非分区表
CREATE TABLE nkuwiki.wechat_articles (
    article_id BIGSERIAL PRIMARY KEY,
    original_url TEXT NOT NULL UNIQUE,
    title VARCHAR(255) NOT NULL,
    publish_time TIMESTAMPTZ NOT NULL,
    nickname VARCHAR(255),
    content_type VARCHAR(50),
    file_path TEXT,
    download_status VARCHAR(20)
);

-- 创建普通索引
CREATE INDEX idx_publish_time ON nkuwiki.wechat_articles (publish_time);
CREATE INDEX idx_url ON nkuwiki.wechat_articles (original_url);

-- 创建视图
-- CREATE OR REPLACE VIEW nkuwiki.recent_articles AS
-- SELECT 
--     article_id,
--     original_url,
--     nickname,
--     title,
--     publish_time AT TIME ZONE 'Asia/Shanghai' AS publish_time_cst,
--     file_path,
--     content_type
-- FROM nkuwiki.wechat_articles
-- ORDER BY publish_time DESC
-- LIMIT 100;

-- 添加注释
COMMENT ON TABLE nkuwiki.wechat_articles IS '微信公众号文章元数据存储';
COMMENT ON COLUMN nkuwiki.wechat_articles.original_url IS '文章原始URL地址';
COMMENT ON COLUMN nkuwiki.wechat_articles.publish_time IS '文章发布时间（UTC时区）';
COMMENT ON COLUMN nkuwiki.wechat_articles.run_time IS '数据抓取时间（UTC时区）';
COMMENT ON COLUMN nkuwiki.wechat_articles.original_meta IS '原始JSON元数据';

-- 最后执行权限设置
GRANT ALL PRIVILEGES ON TABLE nkuwiki.wechat_articles TO nkuwiki_user;

\echo '初始化完成'

-- 后续操作完成后撤销权限
-- ALTER USER nkuwiki_user WITH NOSUPERUSER;