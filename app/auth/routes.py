"""
Authentication Routes
Login, Register, Get Current User
"""
from datetime import timedelta
from fastapi import APIRouter, HTTPException, status, Depends
import logging

from app.auth.models import (
    LoginRequest, Token, User, UserCreate
)
from app.auth.utils import (
    verify_password, create_access_token, get_current_user,
    ACCESS_TOKEN_EXPIRE_HOURS
)
from app.auth.user_store import (
    get_user_by_email, create_user, update_last_login
)

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])
logger = logging.getLogger(__name__)


@router.post("/login", response_model=Token)
async def login(request: LoginRequest) -> Token:
    """
    Authenticate user and return JWT token
    """
    # Find user by email
    user = get_user_by_email(request.email)

    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )

    # Update last login
    update_last_login(user.id)

    # Create token
    access_token = create_access_token(
        data={"sub": user.id, "email": user.email, "role": user.role},
        expires_delta=timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    )

    logger.info(f"User logged in: {user.email}")

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_HOURS * 3600
    )


@router.post("/register", response_model=User)
async def register(user_data: UserCreate) -> User:
    """
    Register a new user
    """
    try:
        new_user = create_user(user_data)
        logger.info(f"New user registered: {new_user.email}")

        return User(
            id=new_user.id,
            email=new_user.email,
            name=new_user.name,
            role=new_user.role,
            created_at=new_user.created_at,
            last_login=new_user.last_login
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/me", response_model=User)
async def get_me(current_user = Depends(get_current_user)) -> User:
    """
    Get current authenticated user's info
    """
    return User(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        role=current_user.role,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )
