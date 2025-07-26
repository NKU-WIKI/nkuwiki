CREATE TABLE IF NOT EXISTS `link_graph` (
    `id` bigint(20) NOT NULL AUTO_INCREMENT,
    `source_url` varchar(255) NOT NULL COMMENT '源页面URL',
    `target_url` varchar(255) NOT NULL COMMENT '目标页面URL',
    `anchor_text` varchar(255) DEFAULT NULL COMMENT '链接锚文本',
    `link_type` varchar(20) DEFAULT 'internal' COMMENT '链接类型：internal-内部链接, external-外部链接',
    `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_source_target` (`source_url`, `target_url`),
    KEY `idx_source_url` (`source_url`),
    KEY `idx_target_url` (`target_url`),
    KEY `idx_link_type` (`link_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='页面链接关系表'; 