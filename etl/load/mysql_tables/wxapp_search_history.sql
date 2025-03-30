CREATE TABLE IF NOT EXISTS wxapp_search_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    openid VARCHAR(64),
    keyword VARCHAR(255) NOT NULL,
    search_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_openid (openid),
    INDEX idx_keyword (keyword),
    INDEX idx_search_time (search_time)
); 