DROP TABLE IF EXISTS `wxapp_search_history`;
CREATE TABLE IF NOT EXISTS `wxapp_search_history` (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL COMMENT '用户ID，关联wxapp_user表',
    query VARCHAR(255) DEFAULT NULL,
    search_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_query (query),
    INDEX idx_search_time (search_time),
    FOREIGN KEY (user_id) REFERENCES wxapp_user(id) ON DELETE CASCADE
);