CREATE TABLE IF NOT EXISTS `wxapp_notifications` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `user_id` VARCHAR(100) NOT NULL COMMENT '接收者用户ID',
    `title` VARCHAR(255) NOT NULL COMMENT '通知标题',
    `content` TEXT NOT NULL COMMENT '通知内容',
    `type` VARCHAR(20) NOT NULL COMMENT '通知类型: system-系统通知, like-点赞, comment-评论, follow-关注',
    `is_read` TINYINT DEFAULT 0 COMMENT '是否已读: 1-已读, 0-未读',
    `sender_id` VARCHAR(100) DEFAULT NULL COMMENT '发送者ID，如系统通知则为null',
    `related_id` VARCHAR(100) DEFAULT NULL COMMENT '关联ID，比如帖子ID或评论ID',
    `related_type` VARCHAR(20) DEFAULT NULL COMMENT '关联类型，如post, comment等',
    `create_time` DATETIME NOT NULL COMMENT '创建时间',
    `update_time` DATETIME NOT NULL COMMENT '更新时间',
    PRIMARY KEY (`id`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_type` (`type`),
    KEY `idx_is_read` (`is_read`),
    KEY `idx_create_time` (`create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='微信小程序通知数据表'; 