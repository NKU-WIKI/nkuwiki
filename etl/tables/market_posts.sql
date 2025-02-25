CREATE TABLE IF NOT EXISTS market_posts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    publish_time DATETIME NOT NULL COMMENT '帖子发布时间',
    title VARCHAR(255) NOT NULL COMMENT '帖子标题',
    content TEXT NOT NULL COMMENT '帖子正文内容',
    author VARCHAR(100) COMMENT '发帖用户',
    original_url VARCHAR(512) UNIQUE NOT NULL COMMENT '帖子原始链接',
    platform VARCHAR(50) DEFAULT 'market' COMMENT '数据来源平台',
    content_type VARCHAR(20) DEFAULT 'post' COMMENT '内容类型（post/comment等）',
    scrape_time DATETIME NOT NULL COMMENT '爬取时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='校园集市帖子数据表'; 