"""认证依赖注入。

提供 FastAPI Depends 用的函数:
- get_current_user: 从 Authorization header 解析 JWT,返回 User ORM
- require_role(*roles): 工厂函数,返回一个限定角色的 Depends

用法:
    @router.get("/me")
    async def me(user: User = Depends(get_current_user)): ...

    @router.get("/admin-only")
    async def admin(user: User = Depends(require_role("admin", "super_admin"))): ...
"""

from collections.abc import Callable, Coroutine
from typing import Any

import jwt as pyjwt
from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import decode_token
from app.db.models.user import User
from app.deps.db import get_db


def _extract_bearer_token(request: Request) -> str:
    """从 Authorization header 提取 Bearer token。"""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise UnauthorizedError(message="缺少认证信息")
    parts = auth_header.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise UnauthorizedError(message="认证格式错误,需 Bearer <token>")
    return parts[1]


async def get_current_user(
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> User:
    """解析 JWT access_token 并返回对应的 User ORM 对象。

    失败场景:
    - 无 Authorization header → 401
    - token 过期 / 签名错误 → 401
    - token type != "access" → 401
    - user_id 不存在 / 已禁用 → 401
    """
    token = _extract_bearer_token(request)

    try:
        payload = decode_token(token)
    except pyjwt.PyJWTError as exc:
        raise UnauthorizedError(message="令牌无效或已过期") from exc

    if payload.get("type") != "access":
        raise UnauthorizedError(message="令牌类型错误")

    user_id = int(payload["sub"])
    stmt = select(User).where(User.id == user_id)
    user = (await session.execute(stmt)).scalar_one_or_none()

    if user is None:
        raise UnauthorizedError(message="用户不存在")
    if user.status != "active":
        raise UnauthorizedError(code="auth.account_disabled", message="账号已禁用")

    return user


def require_role(
    *allowed_roles: str,
) -> Callable[..., Coroutine[Any, Any, User]]:
    """角色限定依赖工厂。

    返回一个 FastAPI 兼容的 async 函数,可用于 Depends():
        Depends(require_role("admin", "super_admin"))

    先走 get_current_user 拿到用户,再检查 role 是否在允许列表中。
    """

    async def _role_checker(
        user: User = Depends(get_current_user),
    ) -> User:
        if user.role not in allowed_roles:
            raise ForbiddenError(message="权限不足")
        return user

    return _role_checker
