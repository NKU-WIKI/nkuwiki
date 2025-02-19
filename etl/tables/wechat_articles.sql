CREATE TABLE IF NOT EXISTS wechat_articles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL COMMENT '文章标题',
    -- content TEXT NULL COMMENT '文章内容',
    publish_time DATETIME NOT NULL COMMENT '发布时间',
    original_url VARCHAR(255) NOT NULL UNIQUE COMMENT '文章链接',
    nickname VARCHAR(100) COMMENT '公众号昵称',
    run_time DATETIME COMMENT '抓取时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;