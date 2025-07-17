CREATE TABLE `wxapp_banwords` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `category_id` INT NOT NULL COMMENT '分类ID',
    `word` VARCHAR(100) NOT NULL COMMENT '违禁词',
    `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY `uk_category_word` (`category_id`, `word`),
    FOREIGN KEY (`category_id`) REFERENCES `wxapp_banword_categories`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='违禁词表'; 