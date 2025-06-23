CREATE TABLE IF NOT EXISTS wxapp_search_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    openid VARCHAR(64),
    query VARCHAR(255) DEFAULT NULL,
    search_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_openid (openid),
    INDEX idx_query (query),
    INDEX idx_search_time (search_time)
); 