"""
Authentication API routes
"""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import Optional
import logging

from .schemas import (
    RegisterRequest, LoginRequest, GoogleAuthRequest,
    TokenResponse, UserResponse, MessageResponse
)
from .security import (
    hash_password, verify_password, create_access_token, verify_google_token
)
from .dependencies import get_current_user

# Import database functions (will be added to db_config.py)
try:
    from database.db_config import (
        create_user, get_user_by_email, get_user_by_google_id,
        create_google_user, get_user_by_id
    )
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/register", response_model=TokenResponse)
async def register(request: RegisterRequest):
    """Register a new user with email and password"""
    if not DB_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available"
        )

    # Check if email already exists
    existing_user = get_user_by_email(request.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Hash password and create user
    password_hash = hash_password(request.password)
    user_id = create_user(request.email, password_hash)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )

    # Create JWT token
    access_token = create_access_token(user_id, request.email)

    logger.info(f"New user registered: {request.email}")
    return TokenResponse(access_token=access_token)


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Login with email and password"""
    if not DB_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available"
        )

    # Get user by email
    user = get_user_by_email(request.email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Check if user registered with Google (no password)
    if user.get('auth_provider') == 'google' and not user.get('password_hash'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This email is registered with Google. Please use Google Sign-In."
        )

    # Verify password
    if not verify_password(request.password, user['password_hash']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Create JWT token
    access_token = create_access_token(user['id'], user['email'])

    logger.info(f"User logged in: {request.email}")
    return TokenResponse(access_token=access_token)


@router.post("/google", response_model=TokenResponse)
async def google_login(request: GoogleAuthRequest):
    """Login or register with Google OAuth"""
    if not DB_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available"
        )

    # Verify Google token
    google_user = verify_google_token(request.credential)

    if not google_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token"
        )

    # Check if user exists by Google ID
    user = get_user_by_google_id(google_user['google_id'])

    if not user:
        # Check if email exists (registered with password)
        existing_user = get_user_by_email(google_user['email'])

        if existing_user:
            # Email exists with password auth - could link accounts
            # For now, we'll return an error
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered with password. Please login with password."
            )

        # Create new Google user
        user_id = create_google_user(
            email=google_user['email'],
            google_id=google_user['google_id']
        )

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user"
            )

        user = {'id': user_id, 'email': google_user['email']}
        logger.info(f"New Google user registered: {google_user['email']}")
    else:
        logger.info(f"Google user logged in: {user['email']}")

    # Create JWT token
    access_token = create_access_token(user['id'], user['email'])

    return TokenResponse(access_token=access_token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    if not DB_AVAILABLE:
        # Return basic info from token if DB not available
        return UserResponse(
            id=current_user['id'],
            email=current_user['email'],
            auth_provider="unknown"
        )

    # Get full user info from database
    user = get_user_by_id(current_user['id'])

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserResponse(
        id=user['id'],
        email=user['email'],
        auth_provider=user.get('auth_provider', 'email')
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(current_user: dict = Depends(get_current_user)):
    """Logout user (client-side token removal)"""
    # JWT tokens are stateless, so logout is handled client-side
    # This endpoint just confirms the token was valid
    logger.info(f"User logged out: {current_user['email']}")
    return MessageResponse(success=True, message="Logged out successfully")
