"""认证路由:注册 / 登录 / 刷新 / 当前用户。

MVP 阶段只做手机号 + 密码(短信接口暂不可用)。

路由清单:
- POST /auth/register → 注册
- POST /auth/login    → 登录
- POST /auth/refresh  → 刷新令牌
- GET  /auth/me       → 获取当前用户信息
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.deps.auth import get_current_user
from app.deps.db import get_db
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserRead,
)
from app.schemas.envelope import ApiResponse
from app.services.auth_service import (
    authenticate_user,
    issue_tokens,
    refresh_tokens,
    register_user,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=ApiResponse[TokenResponse])
async def register(
    body: RegisterRequest,
    session: AsyncSession = Depends(get_db),
) -> ApiResponse[TokenResponse]:
    """注册新用户(手机号 + 密码),成功后自动签发令牌。"""
    user = await register_user(
        session,
        phone=body.phone,
        password=body.password,
        nickname=body.nickname,
    )
    tokens = issue_tokens(user)
    return ApiResponse.success(tokens)


@router.post("/login", response_model=ApiResponse[TokenResponse])
async def login(
    body: LoginRequest,
    session: AsyncSession = Depends(get_db),
) -> ApiResponse[TokenResponse]:
    """手机号 + 密码登录,成功后签发令牌对。"""
    user = await authenticate_user(session, phone=body.phone, password=body.password)
    tokens = issue_tokens(user)
    return ApiResponse.success(tokens)


@router.post("/refresh", response_model=ApiResponse[TokenResponse])
async def refresh(
    body: RefreshRequest,
    session: AsyncSession = Depends(get_db),
) -> ApiResponse[TokenResponse]:
    """用 refresh_token 换发新的令牌对。"""
    tokens = await refresh_tokens(session, refresh_token=body.refresh_token)
    return ApiResponse.success(tokens)


@router.get("/me", response_model=ApiResponse[UserRead])
async def me(
    user: User = Depends(get_current_user),
) -> ApiResponse[UserRead]:
    """获取当前登录用户信息。"""
    return ApiResponse.success(UserRead.model_validate(user))
