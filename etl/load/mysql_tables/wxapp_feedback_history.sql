--
-- 表的结构 `wxapp_feedback_history`
--

CREATE TABLE IF NOT EXISTS `wxapp_feedback_history` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `feedback_id` BIGINT NOT NULL COMMENT '关联的反馈ID',
    `operator` VARCHAR(100) NOT NULL COMMENT '操作员标识',
    `action_type` VARCHAR(50) NOT NULL COMMENT '操作类型 (e.g., "status_change", "reply", "delete")',
    `details` JSON DEFAULT NULL COMMENT '操作详情，如旧状态、新状态或回复内容',
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (`feedback_id`) REFERENCES `wxapp_feedback`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户反馈处理历史表'; 