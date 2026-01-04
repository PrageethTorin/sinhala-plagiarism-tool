# database/db_config.py
import mysql.connector
from mysql.connector import pooling
from typing import List, Dict, Optional
import json
import logging

logger = logging.getLogger(__name__)


# Database Connection 

def get_db_connection():
    """Get a database connection (team style)"""
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",  # Your MySQL password
        database="sinhala_plagiarism_db",
        charset='utf8mb4'  # Critical for Sinhala font support
    )


# Connection pool for better performance
_pool = None

def get_pool():
    """Get or create connection pool"""
    global _pool
    if _pool is None:
        try:
            _pool = pooling.MySQLConnectionPool(
                pool_name="plagiarism_pool",
                pool_size=5,
                pool_reset_session=True,
                host="localhost",
                user="root",
                password="MySql@123",
                database="sinhala_plagiarism_db",
                charset='utf8mb4'
            )
            logger.info("MySQL connection pool created")
        except mysql.connector.Error as err:
            logger.error(f"Pool creation failed: {err}")
            raise
    return _pool


def get_connection():
    """Get connection from pool"""
    try:
        return get_pool().get_connection()
    except:
        # Fallback to simple connection if pool fails
        return get_db_connection()



# Database Initialization


_initialized = False

def initialize_database():
    """Create database and tables if they don't exist"""
    global _initialized
    if _initialized:
        return True

    try:
        # Connect without database first
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="MySql@123",
            charset='utf8mb4'
        )
        cursor = conn.cursor()

        # Create database
        cursor.execute("""
            CREATE DATABASE IF NOT EXISTS sinhala_plagiarism_db
            CHARACTER SET utf8mb4
            COLLATE utf8mb4_unicode_ci
        """)
        cursor.execute("USE sinhala_plagiarism_db")

        # Create tables
        _create_tables(cursor)

        conn.commit()
        cursor.close()
        conn.close()

        _initialized = True
        logger.info("Database initialized successfully")
        return True

    except mysql.connector.Error as err:
        logger.error(f"Database init failed: {err}")
        return False


def _create_tables(cursor):
    """Create all required tables"""

    # Users table for authentication
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NULL,
            google_id VARCHAR(255) NULL,
            auth_provider ENUM('email', 'google') DEFAULT 'email',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_email (email),
            INDEX idx_google_id (google_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    # Plagiarism check history
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS plagiarism_checks (
            id INT AUTO_INCREMENT PRIMARY KEY,
            check_type VARCHAR(50) NOT NULL,
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
            INDEX idx_check_type (check_type)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    # Corpus matches
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
            FOREIGN KEY (check_id) REFERENCES plagiarism_checks(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    # Training pairs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS training_pairs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            sentence_1 TEXT NOT NULL,
            sentence_2 TEXT NOT NULL,
            similarity_label FLOAT,
            source VARCHAR(100),
            is_verified BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    logger.info("Tables created successfully")



# Plagiarism Check History Functions


def save_check(check_type: str, original_text: str, suspicious_text: str = None,
               file_name: str = None, similarity_score: float = None,
               is_plagiarized: bool = None, algorithm_used: str = None,
               threshold_applied: float = None, processing_time: float = None,
               components: Dict = None, metadata: Dict = None) -> Optional[int]:
    """Save a plagiarism check to database"""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO plagiarism_checks
            (check_type, original_text, suspicious_text, file_name,
             similarity_score, is_plagiarized, algorithm_used,
             threshold_applied, processing_time, components, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            check_type,
            original_text[:65535] if original_text else None,
            suspicious_text[:65535] if suspicious_text else None,
            file_name,
            similarity_score,
            is_plagiarized,
            algorithm_used,
            threshold_applied,
            processing_time,
            json.dumps(components) if components else None,
            json.dumps(metadata) if metadata else None
        ))

        check_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
        return check_id

    except mysql.connector.Error as err:
        logger.error(f"Save check failed: {err}")
        return None


def get_history(limit: int = 50, offset: int = 0, check_type: str = None) -> List[Dict]:
    """Get plagiarism check history"""
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        query = "SELECT * FROM plagiarism_checks WHERE 1=1"
        params = []

        if check_type:
            query += " AND check_type = %s"
            params.append(check_type)

        query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        cursor.execute(query, params)
        results = cursor.fetchall()

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
        logger.error(f"Get history failed: {err}")
        return []


def get_statistics(days: int = 30) -> Dict:
    """Get usage statistics"""
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

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

        cursor.execute("""
            SELECT check_type, COUNT(*) as count
            FROM plagiarism_checks
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
            GROUP BY check_type
        """, (days,))
        stats['by_type'] = {row['check_type']: row['count'] for row in cursor.fetchall()}

        cursor.close()
        conn.close()
        return stats

    except mysql.connector.Error as err:
        logger.error(f"Get stats failed: {err}")
        return {}


def db_health_check() -> Dict:
    """Check database connectivity"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        conn.close()
        return {"status": "healthy", "database": "sinhala_plagiarism_db"}
    except mysql.connector.Error as err:
        return {"status": "unhealthy", "error": str(err)}



# User Authentication CRUD Functions


def create_user(email: str, password_hash: str) -> Optional[int]:
    """Create a new user with email and password"""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO users (email, password_hash, auth_provider)
            VALUES (%s, %s, 'email')
        """, (email, password_hash))

        user_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
        return user_id

    except mysql.connector.Error as err:
        logger.error(f"Create user failed: {err}")
        return None


def create_google_user(email: str, google_id: str) -> Optional[int]:
    """Create a new user with Google OAuth"""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO users (email, google_id, auth_provider)
            VALUES (%s, %s, 'google')
        """, (email, google_id))

        user_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
        return user_id

    except mysql.connector.Error as err:
        logger.error(f"Create Google user failed: {err}")
        return None


def get_user_by_email(email: str) -> Optional[Dict]:
    """Get user by email address"""
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, email, password_hash, google_id, auth_provider, created_at
            FROM users WHERE email = %s
        """, (email,))

        user = cursor.fetchone()
        cursor.close()
        conn.close()
        return user

    except mysql.connector.Error as err:
        logger.error(f"Get user by email failed: {err}")
        return None


def get_user_by_google_id(google_id: str) -> Optional[Dict]:
    """Get user by Google ID"""
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, email, password_hash, google_id, auth_provider, created_at
            FROM users WHERE google_id = %s
        """, (google_id,))

        user = cursor.fetchone()
        cursor.close()
        conn.close()
        return user

    except mysql.connector.Error as err:
        logger.error(f"Get user by Google ID failed: {err}")
        return None


def get_user_by_id(user_id: int) -> Optional[Dict]:
    """Get user by ID"""
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, email, password_hash, google_id, auth_provider, created_at
            FROM users WHERE id = %s
        """, (user_id,))

        user = cursor.fetchone()
        cursor.close()
        conn.close()
        return user

    except mysql.connector.Error as err:
        logger.error(f"Get user by ID failed: {err}")
        return None
