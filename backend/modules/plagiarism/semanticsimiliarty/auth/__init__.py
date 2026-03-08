"""
Authentication module for Sinhala Plagiarism Detection Tool
"""
from .routes import router as auth_router
from .dependencies import get_current_user, get_optional_user
from .security import hash_password, verify_password, create_access_token

__all__ = [
    'auth_router',
    'get_current_user',
    'get_optional_user',
    'hash_password',
    'verify_password',
    'create_access_token'
]
