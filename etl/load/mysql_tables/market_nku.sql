CREATE TABLE IF NOT EXISTS `market_nku` (
    `id` bigint(20) NOT NULL AUTO_INCREMENT,
    `original_url` varchar(255) NOT NULL COMMENT '原始url',
    `title` varchar(255) NOT NULL COMMENT '标题',
    `content` text NOT NULL COMMENT '内容',
    `author` varchar(64) NOT NULL DEFAULT '' COMMENT '发布者',
    `category` varchar(64) NOT NULL DEFAULT '' COMMENT '分类',
    `image` json DEFAULT NULL COMMENT '图片列表',
    `status` tinyint(4) NOT NULL DEFAULT '1' COMMENT '状态：1-正常，0-结束',
    `view_count` int(11) NOT NULL DEFAULT '0' COMMENT '浏览数',
    `like_count` int(11) NOT NULL DEFAULT '0' COMMENT '点赞数',
    `platform` varchar(64) NOT NULL DEFAULT '' COMMENT '平台',
    `publish_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '发布时间',
    `comment_count` int(11) NOT NULL DEFAULT '0' COMMENT '评论数',
    `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    KEY `idx_status` (`status`),
    KEY `idx_publish_time` (`publish_time`),
    FULLTEXT KEY `ft_content` (`content`, `title`) WITH PARSER ngram
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='南开大学校园集市表'; 