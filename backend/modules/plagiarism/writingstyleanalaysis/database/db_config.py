import os
from pathlib import Path

import mysql.connector


def _load_env():
    try:
        from dotenv import load_dotenv
    except ImportError:
        return

    for parent in Path(__file__).resolve().parents:
        env_path = parent / ".env"
        if env_path.exists():
            load_dotenv(env_path)
            return


_load_env()


def get_db_config(database=None):
    db_name = database or os.getenv("MYSQL_DATABASE", "sinhala_plagiarism_db")
    return {
        "host": os.getenv("MYSQL_HOST", "localhost"),
        "user": os.getenv("MYSQL_USER", "root"),
        "password": os.getenv("MYSQL_PASSWORD", ""),
        "database": db_name,
        "charset": "utf8mb4",
    }


def get_db_connection():
    return mysql.connector.connect(**get_db_config())
