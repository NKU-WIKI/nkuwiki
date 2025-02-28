CREATE TABLE IF NOT EXISTS web_articles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    platform VARCHAR(20) NOT NULL COMMENT '平台',
    original_url VARCHAR(255) NOT NULL UNIQUE COMMENT '文章链接',
    title VARCHAR(255) NOT NULL COMMENT '文章标题',
    author VARCHAR(100) COMMENT '作者',
    publish_time DATETIME NOT NULL COMMENT '发布时间',
    scrape_time DATETIME COMMENT '抓取时间',
    -- content_type VARCHAR(20) NULL COMMENT '内容类型'
    -- content TEXT NULL COMMENT '文章内容',
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;