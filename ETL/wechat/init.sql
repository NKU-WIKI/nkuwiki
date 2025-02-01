-- 创建主表
CREATE TABLE nkuwiki.wechat_articles (
    article_id BIGSERIAL,
    file_path TEXT NOT NULL,
    original_url TEXT,
    nickname VARCHAR(255) NOT NULL,
    title VARCHAR(255) NOT NULL,
    publish_date DATE NOT NULL,
    publish_time TIMESTAMPTZ,
    run_time TIMESTAMPTZ NOT NULL,
    content_type VARCHAR(50) NOT NULL,
    author VARCHAR(255),
    read_count INT DEFAULT 0,
    like_count INT DEFAULT 0,
    original_meta JSONB NOT NULL,
    scrape_status VARCHAR(20) NOT NULL DEFAULT 'pending' 
        CHECK (scrape_status IN ('success', 'failed', 'pending')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- 分区键改为日期类型
    PRIMARY KEY (article_id, publish_date),
    UNIQUE (file_path, publish_date)
) PARTITION BY RANGE (publish_date);

-- 创建索引
CREATE INDEX idx_publish_time ON wechat_articles USING BRIN(publish_time);
CREATE INDEX idx_nickname ON wechat_articles(nickname);
CREATE INDEX idx_original_url ON wechat_articles(original_url);
CREATE INDEX idx_title_search ON wechat_articles USING GIN(to_tsvector('chinese', title));

-- 创建 2025 年分区表
CREATE TABLE IF NOT EXISTS wechat_articles_2025 PARTITION OF wechat_articles
    FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');

-- 添加显式错误日志
ALTER TABLE wechat_articles_2025 
    ADD CONSTRAINT check_year CHECK (publish_date BETWEEN '2025-01-01' AND '2025-12-31');

-- 修改默认分区声明
CREATE TABLE wechat_articles_default PARTITION OF wechat_articles DEFAULT;

-- 创建视图
CREATE OR REPLACE VIEW recent_articles AS
SELECT 
    article_id,
    original_url,
    nickname,
    title,
    publish_time AT TIME ZONE 'Asia/Shanghai' AS publish_time_cst,
    file_path,
    content_type
FROM wechat_articles
ORDER BY publish_time DESC
LIMIT 100;

-- 添加注释
COMMENT ON TABLE wechat_articles IS '微信公众号文章元数据存储';
COMMENT ON COLUMN wechat_articles.original_url IS '文章原始URL地址';
COMMENT ON COLUMN wechat_articles.publish_time IS '文章发布时间（UTC时区）';
COMMENT ON COLUMN wechat_articles.run_time IS '数据抓取时间（UTC时区）';
COMMENT ON COLUMN wechat_articles.original_meta IS '原始JSON元数据';