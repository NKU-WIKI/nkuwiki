-- 更新wxapp_posts表，添加收藏功能相关字段
ALTER TABLE `wxapp_posts` 
ADD COLUMN `favorite_count` INT NOT NULL DEFAULT 0 COMMENT '收藏数量' AFTER `likes`;

-- 更新现有记录，根据favorite_users字段计算并填充favorite_count
UPDATE `wxapp_posts` 
SET `favorite_count` = JSON_LENGTH(IFNULL(`favorite_users`, '[]'));

-- 如果favorite_users为NULL，初始化为空数组
UPDATE `wxapp_posts` 
SET `favorite_users` = '[]' 
WHERE `favorite_users` IS NULL; 