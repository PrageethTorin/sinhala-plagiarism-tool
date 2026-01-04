"""
Database Service for Semantic Similarity Module
Handles MySQL connection and CRUD operations for plagiarism check history
"""
import mysql.connector
from mysql.connector import pooling
from datetime import datetime
from typing import List, Dict, Optional, Any
import json
import os
import logging

logger = logging.getLogger(__name__)


class DatabaseService:
    """MySQL Database Service with connection pooling"""

    _pool = None
    _initialized = False

    # Database configuration
    DB_CONFIG = {
        'host': os.getenv('MYSQL_HOST', 'localhost'),
        'user': os.getenv('MYSQL_USER', 'root'),
        'password': os.getenv('MYSQL_PASSWORD', 'root'),
        'database': os.getenv('MYSQL_DATABASE', 'sinhala_plagiarism_db'),
        'charset': 'utf8mb4',
        'collation': 'utf8mb4_unicode_ci'
    }

    @classmethod
    def get_pool(cls):
        """Get or create connection pool"""
        if cls._pool is None:
            try:
                cls._pool = pooling.MySQLConnectionPool(
                    pool_name="plagiarism_pool",
                    pool_size=5,
                    pool_reset_session=True,
                    **cls.DB_CONFIG
                )
                logger.info("MySQL connection pool created successfully")
            except mysql.connector.Error as err:
                logger.error(f"Failed to create connection pool: {err}")
                raise
        return cls._pool

    @classmethod
    def get_connection(cls):
        """Get connection from pool"""
        return cls.get_pool().get_connection()

    @classmethod
    def initialize_database(cls):
        """Create database and tables if they don't exist"""
        if cls._initialized:
            return True

        try:
            # First connect without database to create it
            config_without_db = cls.DB_CONFIG.copy()
            del config_without_db['database']

            conn = mysql.connector.connect(**config_without_db)
            cursor = conn.cursor()

            # Create database
            cursor.execute(f"""
                CREATE DATABASE IF NOT EXISTS {cls.DB_CONFIG['database']}
                CHARACTER SET utf8mb4
                COLLATE utf8mb4_unicode_ci
            """)
            cursor.execute(f"USE {cls.DB_CONFIG['database']}")

            # Create tables
            cls._create_tables(cursor)

            conn.commit()
            cursor.close()
            conn.close()

            cls._initialized = True
            logger.info("Database initialized successfully")
            return True

        except mysql.connector.Error as err:
            logger.error(f"Database initialization failed: {err}")
            return False

    @classmethod
    def _create_tables(cls, cursor):
        """Create all required tables"""

        # Plagiarism check history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS plagiarism_checks (
                id INT AUTO_INCREMENT PRIMARY KEY,
                check_type ENUM('direct', 'file', 'web_corpus', 'web_search', 'comprehensive') NOT NULL,
                original_text TEXT,
                suspicious_text TEXT,
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
                INDEX idx_check_type (check_type),
                INDEX idx_is_plagiarized (is_plagiarized)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)

        # Web corpus matches table
        cursor.execute("""
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
                FOREIGN KEY (check_id) REFERENCES plagiarism_checks(id) ON DELETE CASCADE,
                INDEX idx_check_id (check_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)

        # Training data pairs table (for model improvement)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS training_pairs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                sentence_1 TEXT NOT NULL,
                sentence_2 TEXT NOT NULL,
                similarity_label FLOAT,
                source VARCHAR(100),
                is_verified BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_source (source),
                INDEX idx_verified (is_verified)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)

        # Users table (optional, for future auth)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255),
                role ENUM('user', 'admin') DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP NULL,
                is_active BOOLEAN DEFAULT TRUE,
                INDEX idx_username (username),
                INDEX idx_email (email)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)

        logger.info("All tables created successfully")

    @classmethod
    def save_plagiarism_check(cls,
                              check_type: str,
                              original_text: str,
                              suspicious_text: str = None,
                              file_name: str = None,
                              similarity_score: float = None,
                              is_plagiarized: bool = None,
                              algorithm_used: str = None,
                              threshold_applied: float = None,
                              processing_time: float = None,
                              components: Dict = None,
                              metadata: Dict = None,
                              user_id: int = None) -> Optional[int]:
        """Save a plagiarism check to database"""
        try:
            conn = cls.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO plagiarism_checks
                (check_type, original_text, suspicious_text, file_name,
                 similarity_score, is_plagiarized, algorithm_used,
                 threshold_applied, processing_time, components, metadata, user_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                check_type,
                original_text[:65535] if original_text else None,  # TEXT limit
                suspicious_text[:65535] if suspicious_text else None,
                file_name,
                similarity_score,
                is_plagiarized,
                algorithm_used,
                threshold_applied,
                processing_time,
                json.dumps(components) if components else None,
                json.dumps(metadata) if metadata else None,
                user_id
            ))

            check_id = cursor.lastrowid
            conn.commit()
            cursor.close()
            conn.close()

            logger.info(f"Saved plagiarism check with ID: {check_id}")
            return check_id

        except mysql.connector.Error as err:
            logger.error(f"Failed to save plagiarism check: {err}")
            return None

    @classmethod
    def save_corpus_match(cls,
                          check_id: int,
                          matched_text: str,
                          source_title: str = None,
                          source_url: str = None,
                          similarity_score: float = None,
                          case_type: str = None,
                          custom_score: float = None,
                          embedding_score: float = None) -> Optional[int]:
        """Save a corpus match result"""
        try:
            conn = cls.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO corpus_matches
                (check_id, matched_text, source_title, source_url,
                 similarity_score, case_type, custom_score, embedding_score)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                check_id,
                matched_text[:65535] if matched_text else None,
                source_title,
                source_url,
                similarity_score,
                case_type,
                custom_score,
                embedding_score
            ))

            match_id = cursor.lastrowid
            conn.commit()
            cursor.close()
            conn.close()

            return match_id

        except mysql.connector.Error as err:
            logger.error(f"Failed to save corpus match: {err}")
            return None

    @classmethod
    def get_check_history(cls,
                          limit: int = 50,
                          offset: int = 0,
                          check_type: str = None,
                          user_id: int = None) -> List[Dict]:
        """Get plagiarism check history"""
        try:
            conn = cls.get_connection()
            cursor = conn.cursor(dictionary=True)

            query = "SELECT * FROM plagiarism_checks WHERE 1=1"
            params = []

            if check_type:
                query += " AND check_type = %s"
                params.append(check_type)

            if user_id:
                query += " AND user_id = %s"
                params.append(user_id)

            query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])

            cursor.execute(query, params)
            results = cursor.fetchall()

            # Parse JSON fields
            for row in results:
                if row.get('components'):
                    row['components'] = json.loads(row['components'])
                if row.get('metadata'):
                    row['metadata'] = json.loads(row['metadata'])
                if row.get('created_at'):
                    row['created_at'] = row['created_at'].isoformat()

            cursor.close()
            conn.close()

            return results

        except mysql.connector.Error as err:
            logger.error(f"Failed to get check history: {err}")
            return []

    @classmethod
    def get_check_by_id(cls, check_id: int) -> Optional[Dict]:
        """Get a specific check by ID with its matches"""
        try:
            conn = cls.get_connection()
            cursor = conn.cursor(dictionary=True)

            # Get the check
            cursor.execute("SELECT * FROM plagiarism_checks WHERE id = %s", (check_id,))
            check = cursor.fetchone()

            if check:
                # Parse JSON
                if check.get('components'):
                    check['components'] = json.loads(check['components'])
                if check.get('metadata'):
                    check['metadata'] = json.loads(check['metadata'])
                if check.get('created_at'):
                    check['created_at'] = check['created_at'].isoformat()

                # Get associated matches
                cursor.execute("""
                    SELECT * FROM corpus_matches WHERE check_id = %s
                """, (check_id,))
                check['matches'] = cursor.fetchall()

                for match in check['matches']:
                    if match.get('created_at'):
                        match['created_at'] = match['created_at'].isoformat()

            cursor.close()
            conn.close()

            return check

        except mysql.connector.Error as err:
            logger.error(f"Failed to get check by ID: {err}")
            return None

    @classmethod
    def get_statistics(cls, days: int = 30) -> Dict:
        """Get usage statistics for the last N days"""
        try:
            conn = cls.get_connection()
            cursor = conn.cursor(dictionary=True)

            # Total checks
            cursor.execute("""
                SELECT
                    COUNT(*) as total_checks,
                    COUNT(CASE WHEN is_plagiarized = TRUE THEN 1 END) as plagiarized_count,
                    AVG(similarity_score) as avg_similarity,
                    AVG(processing_time) as avg_processing_time
                FROM plagiarism_checks
                WHERE created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
            """, (days,))
            stats = cursor.fetchone()

            # Checks by type
            cursor.execute("""
                SELECT check_type, COUNT(*) as count
                FROM plagiarism_checks
                WHERE created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
                GROUP BY check_type
            """, (days,))
            stats['by_type'] = {row['check_type']: row['count'] for row in cursor.fetchall()}

            # Daily trend
            cursor.execute("""
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM plagiarism_checks
                WHERE created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
                GROUP BY DATE(created_at)
                ORDER BY date
            """, (days,))
            stats['daily_trend'] = [
                {'date': row['date'].isoformat(), 'count': row['count']}
                for row in cursor.fetchall()
            ]

            cursor.close()
            conn.close()

            return stats

        except mysql.connector.Error as err:
            logger.error(f"Failed to get statistics: {err}")
            return {}

    @classmethod
    def delete_check(cls, check_id: int) -> bool:
        """Delete a check and its associated matches"""
        try:
            conn = cls.get_connection()
            cursor = conn.cursor()

            cursor.execute("DELETE FROM plagiarism_checks WHERE id = %s", (check_id,))
            affected = cursor.rowcount

            conn.commit()
            cursor.close()
            conn.close()

            return affected > 0

        except mysql.connector.Error as err:
            logger.error(f"Failed to delete check: {err}")
            return False

    @classmethod
    def health_check(cls) -> Dict:
        """Check database connectivity"""
        try:
            conn = cls.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            conn.close()

            return {
                "status": "healthy",
                "database": cls.DB_CONFIG['database'],
                "host": cls.DB_CONFIG['host']
            }
        except mysql.connector.Error as err:
            return {
                "status": "unhealthy",
                "error": str(err)
            }


# Singleton instance
db_service = DatabaseService()
