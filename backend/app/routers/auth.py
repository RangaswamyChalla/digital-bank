from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, Cookie
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.schemas.auth import LoginRequest, RegisterRequest, Token
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


def _set_token_cookies(response: Response, access_token: str, refresh_token: str):
    """Set httpOnly cookies for tokens"""
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,  # HTTPS only in production
        samesite="lax",
        max_age=15 * 60  # 15 minutes
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=7 * 24 * 60 * 60  # 7 days
    )


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, response: Response, db: AsyncSession = Depends(get_db)):
    """Register a new user and return access tokens"""
    user = await AuthService.register(db, request)
    # Auto-login after registration
    login_request = LoginRequest(email=user.email, password=request.password)
    token_data = await AuthService.login(db, login_request)

    _set_token_cookies(response, token_data.access_token, token_data.refresh_token)

    return {
        "access_token": token_data.access_token,
        "refresh_token": token_data.refresh_token,
        "token_type": "bearer"
    }


@router.post("/login")
async def login(request: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    """Login with email and password"""
    try:
        result = await AuthService.login(db, request)

        _set_token_cookies(response, result.access_token, result.refresh_token)

        return {
            "access_token": result.access_token,
            "refresh_token": result.refresh_token,
            "token_type": "bearer"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.post("/refresh", response_model=Token)
async def refresh(
    response: Response,
    refresh_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Refresh access token using refresh token from cookie"""
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found in cookies"
        )

    token_data = await AuthService.refresh(db, refresh_token)

    # Set new cookies with rotated tokens
    _set_token_cookies(response, token_data.access_token, token_data.refresh_token)

    return {
        "access_token": token_data.access_token,
        "refresh_token": token_data.refresh_token,
        "token_type": "bearer"
    }


@router.post("/logout")
async def logout(
    response: Response,
    refresh_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    """Logout and invalidate refresh token"""
    if refresh_token:
        await AuthService.logout(db, refresh_token)

    # Clear cookies
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")

    return {"message": "Logged out successfully"}
