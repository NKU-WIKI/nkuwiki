CREATE TABLE IF NOT EXISTS `website_nku` (
    `id` bigint(20) NOT NULL AUTO_INCREMENT,
    `original_url` varchar(255) NOT NULL COMMENT '原始url',
    `title` varchar(500) NOT NULL COMMENT '标题',
    `content` text NOT NULL COMMENT '内容',
    `author` varchar(64) NOT NULL DEFAULT '' COMMENT '作者',
    `publish_time` datetime DEFAULT NULL COMMENT '发布时间',
    `scrape_time` datetime DEFAULT NULL COMMENT '爬取时间',
    `platform` varchar(64) NOT NULL DEFAULT '' COMMENT '平台',
    `view_count` int(11) NOT NULL DEFAULT '0' COMMENT '浏览数',
    `pagerank_score` double NOT NULL DEFAULT '0' COMMENT 'PageRank分数',
    `is_official` tinyint(1) NULL DEFAULT '0' COMMENT '是否为官方信息',
    `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_original_url` (`original_url`),
    KEY `idx_publish_time` (`publish_time`),
    FULLTEXT KEY `ft_content` (`content`, `title`) WITH PARSER ngram
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='南开大学网站文章表'; 