CREATE TABLE IF NOT EXISTS `pagerank_scores` (
    `id` bigint(20) NOT NULL AUTO_INCREMENT,
    `url` varchar(255) NOT NULL COMMENT '页面URL',
    `pagerank_score` double NOT NULL DEFAULT '0' COMMENT 'PageRank分数',
    `in_degree` int(11) NOT NULL DEFAULT '0' COMMENT '入度（指向该页面的链接数）',
    `out_degree` int(11) NOT NULL DEFAULT '0' COMMENT '出度（该页面指向其他页面的链接数）',
    `calculation_date` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'PageRank计算时间',
    `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_url` (`url`),
    KEY `idx_pagerank_score` (`pagerank_score` DESC),
    KEY `idx_calculation_date` (`calculation_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='PageRank分数表'; 