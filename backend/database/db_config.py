# database/db_config.py
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
        password="MySql@123",  # Your MySQL password
        database="sinhala_plagiarism_db",
        charset='utf8mb4'  # Critical for Sinhala font support
    )
