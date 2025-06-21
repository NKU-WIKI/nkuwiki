-- 结构化洞察信息表
CREATE TABLE IF NOT EXISTS `insights` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `title` VARCHAR(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '洞察标题',
  `content` TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '洞察主体内容',
  `tags` JSON COMMENT '洞察标签列表',
  `category` VARCHAR(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT '综合' COMMENT '洞察分类 (e.g., 学术科研, 校园生活, 通知公告)',
  `insight_date` DATE NOT NULL COMMENT '洞察相关的日期',
  `source_node_ids` JSON COMMENT '生成此洞察所依据的源节点ID列表',
  `relevance_score` FLOAT DEFAULT 0.0 COMMENT '相关性或热度分数',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  KEY `idx_insight_date_category` (`insight_date`, `category`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='结构化洞察信息表'; 