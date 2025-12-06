-- 声纹识别数据库创建脚本
-- 
-- 推荐使用方法（使用自动化脚本）：
-- cd /Users/hanli/Desktop/DeepDiary
-- ./script/setup-voiceprint-db.sh
--
-- 或者直接执行 SQL：
-- docker exec -i xiaozhi-esp32-server-db mysql -u root -p123456 < create_voiceprint_db.sql

-- 创建数据库
CREATE DATABASE IF NOT EXISTS voiceprint_db 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

-- 使用数据库
USE voiceprint_db;

-- 创建声纹表
CREATE TABLE IF NOT EXISTS voiceprints (
    id INT AUTO_INCREMENT PRIMARY KEY,
    speaker_id VARCHAR(255) NOT NULL UNIQUE COMMENT '说话人ID',
    feature_vector LONGBLOB NOT NULL COMMENT '声纹特征向量',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_speaker_id (speaker_id)
) ENGINE=InnoDB 
DEFAULT CHARSET=utf8mb4 
COLLATE=utf8mb4_unicode_ci 
COMMENT='声纹识别数据表';

-- 验证创建结果
SHOW DATABASES LIKE 'voiceprint_db';
SHOW TABLES;
DESCRIBE voiceprints;

