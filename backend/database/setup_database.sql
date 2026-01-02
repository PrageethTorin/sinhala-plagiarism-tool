-- Run: mysql -u root -p < setup_database.sql


-- Create database with Sinhala/Unicode support
CREATE DATABASE IF NOT EXISTS sinhala_plagiarism_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE sinhala_plagiarism_db;

-- Plagiarism check history
CREATE TABLE IF NOT EXISTS plagiarism_checks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    check_type VARCHAR(50) NOT NULL COMMENT 'direct, file, web_corpus, web_search, comprehensive',
    original_text TEXT COMMENT 'Text being checked',
    suspicious_text TEXT COMMENT 'Comparison text',
    file_name VARCHAR(255),
    similarity_score FLOAT,
    is_plagiarized BOOLEAN,
    algorithm_used VARCHAR(50),
    threshold_applied FLOAT,
    processing_time FLOAT,
    components JSON,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id INT DEFAULT NULL,
    INDEX idx_created_at (created_at),
    INDEX idx_check_type (check_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Corpus matches
CREATE TABLE IF NOT EXISTS corpus_matches (
    id INT AUTO_INCREMENT PRIMARY KEY,
    check_id INT,
    matched_text TEXT,
    source_title VARCHAR(500),
    source_url VARCHAR(2048),
    similarity_score FLOAT,
    case_type VARCHAR(50),
    custom_score FLOAT,
    embedding_score FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (check_id) REFERENCES plagiarism_checks(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Training pairs for model improvement
CREATE TABLE IF NOT EXISTS training_pairs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sentence_1 TEXT NOT NULL,
    sentence_2 TEXT NOT NULL,
    similarity_label FLOAT,
    source VARCHAR(100),
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Success message
SELECT 'Database created successfully!' AS status;
SHOW TABLES;
