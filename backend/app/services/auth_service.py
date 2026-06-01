"""认证业务逻辑。

职责:注册新用户、验证登录凭据、签发令牌、刷新令牌。
所有数据库操作通过注入的 AsyncSession 完成,不持有状态。
"""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import AppException, UnauthorizedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.db.models.user import User
from app.schemas.auth import TokenResponse


class PhoneAlreadyRegisteredError(AppException):
    """手机号已注册(409 Conflict)。"""

    code = "auth.phone_already_registered"
    status_code = 409


async def register_user(
    session: AsyncSession,
    *,
    phone: str,
    password: str,
    nickname: str | None = None,
) -> User:
    """注册新用户(手机号 + 密码)。

    检查手机号唯一性,哈希密码后写入 DB。返回新创建的 User ORM 对象。
    """
    # 检查手机号是否已存在
    stmt = select(User).where(User.phone == phone)
    existing = (await session.execute(stmt)).scalar_one_or_none()
    if existing is not None:
        raise PhoneAlreadyRegisteredError(message="该手机号已注册")

    user = User(
        phone=phone,
        password_hash=hash_password(password),
        nickname=nickname,
        role="free_user",
        status="active",
    )
    session.add(user)
    await session.flush()
    return user


async def authenticate_user(
    session: AsyncSession,
    *,
    phone: str,
    password: str,
) -> User:
    """验证手机号 + 密码,成功返回 User,失败抛 UnauthorizedError。"""
    stmt = select(User).where(User.phone == phone)
    user = (await session.execute(stmt)).scalar_one_or_none()

    if user is None:
        raise UnauthorizedError(code="auth.invalid_credentials", message="手机号或密码错误")

    if user.status != "active":
        raise UnauthorizedError(code="auth.account_disabled", message="账号已禁用")

    if not user.password_hash:
        raise UnauthorizedError(code="auth.no_password", message="该账号未设置密码")

    if not verify_password(password, user.password_hash):
        raise UnauthorizedError(code="auth.invalid_credentials", message="手机号或密码错误")

    # 更新最近登录时间
    user.last_login_at = datetime.now(UTC)
    return user


def issue_tokens(user: User) -> TokenResponse:
    """为已认证用户签发 access + refresh 令牌对。"""
    settings = get_settings()
    access = create_access_token(user.id, user.role)
    refresh = create_refresh_token(user.id)
    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        expires_in=settings.jwt_access_expire_minutes * 60,
    )


async def refresh_tokens(session: AsyncSession, *, refresh_token: str) -> TokenResponse:
    """用 refresh_token 换发新的令牌对。

    验证 refresh_token 有效性,重新查库获取最新 role(防止用户权限变更后旧 token 残留)。
    """
    import jwt as pyjwt

    try:
        payload = decode_token(refresh_token)
    except pyjwt.PyJWTError as exc:
        raise UnauthorizedError(
            code="auth.invalid_refresh_token", message="刷新令牌无效或已过期"
        ) from exc

    if payload.get("type") != "refresh":
        raise UnauthorizedError(code="auth.invalid_token_type", message="令牌类型错误")

    user_id = int(payload["sub"])
    stmt = select(User).where(User.id == user_id)
    user = (await session.execute(stmt)).scalar_one_or_none()

    if user is None or user.status != "active":
        raise UnauthorizedError(code="auth.user_not_found", message="用户不存在或已禁用")

    return issue_tokens(user)
