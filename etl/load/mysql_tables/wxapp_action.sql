CREATE TABLE IF NOT EXISTS `wxapp_action` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `openid` VARCHAR(100) NOT NULL COMMENT '执行者openid',
    `action_type` VARCHAR(100) NOT NULL COMMENT '动作类型：like-点赞, comment-评论, follow-关注',
    `target_id` INT DEFAULT NULL COMMENT '目标ID，如帖子ID、评论ID等',
    `target_type` VARCHAR(100) DEFAULT NULL COMMENT '目标类型，如post、comment等',
    `extra_data` JSON DEFAULT NULL COMMENT '额外数据',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    KEY `idx_openid` (`openid`),
    KEY `idx_action_type` (`action_type`),
    KEY `idx_target` (`target_id`, `target_type`),
    KEY `idx_create_time` (`create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户动作表'; 