CREATE TABLE IF NOT EXISTS `wxapp_feedback` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `openid` VARCHAR(100) NOT NULL COMMENT '用户openid',
    `content` TEXT NOT NULL COMMENT '反馈内容',
    `type` VARCHAR(20) NOT NULL COMMENT '反馈类型: bug-功能异常, feature-功能建议, content-内容问题, other-其他',
    `contact` VARCHAR(100) DEFAULT NULL COMMENT '联系方式，如邮箱、微信等',
    `images` JSON COMMENT '反馈图片列表',
    `device_info` JSON COMMENT '设备信息',
    `status` TINYINT DEFAULT 0 COMMENT '处理状态: 0-待处理, 1-处理中, 2-已处理, 3-已关闭',
    `admin_reply` TEXT DEFAULT NULL COMMENT '管理员回复',
    `extra` JSON COMMENT '扩展字段，存储额外信息',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `resolve_time` DATETIME DEFAULT NULL COMMENT '解决时间',
    `platform` VARCHAR(20) DEFAULT 'wxapp' COMMENT '平台标识',
    `is_deleted` TINYINT DEFAULT 0 COMMENT '是否删除：1-已删除, 0-未删除',
    PRIMARY KEY (`id`),
    KEY `idx_openid` (`openid`),
    KEY `idx_type` (`type`),
    KEY `idx_status` (`status`),
    KEY `idx_create_time` (`create_time`),
    FULLTEXT KEY `ft_content` (`content`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='微信小程序反馈数据表'; 