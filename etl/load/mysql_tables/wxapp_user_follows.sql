CREATE TABLE IF NOT EXISTS `wxapp_user_follows` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `follower_id` VARCHAR(100) NOT NULL COMMENT '关注者的openid',
    `followed_id` VARCHAR(100) NOT NULL COMMENT '被关注者的openid',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '关注时间',
    `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `status` TINYINT DEFAULT 1 COMMENT '状态：1-正常, 0-已取消',
    `is_deleted` TINYINT DEFAULT 0 COMMENT '是否删除：1-已删除, 0-未删除',
    PRIMARY KEY (`id`),
    UNIQUE KEY `unq_follower_followed` (`follower_id`, `followed_id`),
    KEY `idx_follower_id` (`follower_id`),
    KEY `idx_followed_id` (`followed_id`),
    KEY `idx_create_time` (`create_time`),
    KEY `idx_status` (`status`, `is_deleted`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户关注关系表'; 