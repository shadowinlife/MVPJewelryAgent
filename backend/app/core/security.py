"""安全工具:JWT 令牌 + 密码哈希。

JWT 策略:
- access_token: 短命令牌(默认 30 分钟),携带 user_id + role;
- refresh_token: 长命令牌(默认 7 天),只携带 user_id + type="refresh"。
- 签名算法 HS256;密钥来自 Settings.jwt_secret。

密码哈希:
- 直接使用 bcrypt 库(passlib 与 bcrypt>=5.0 有兼容问题,弃用)。
"""

from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt

from app.core.config import get_settings

# --- 密码哈希 ---


def hash_password(plain: str) -> str:
    """将明文密码转为 bcrypt 哈希。"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """校验明文与哈希是否匹配。"""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


# --- JWT ---

_ALGORITHM = "HS256"

# PyJWT >= 2.8 对 HS256 要求密钥 >= 32 bytes;dev fallback 必须满足此最低长度
_DEV_FALLBACK_SECRET = "INSECURE-DEV-JWT-SECRET-DO-NOT-USE-IN-PRODUCTION-CHANGEME"


def _get_secret() -> str:
    """获取 JWT 签名密钥;空值时使用 fallback(仅 local 开发)。"""
    secret = get_settings().jwt_secret
    if not secret:
        return _DEV_FALLBACK_SECRET
    return secret


def create_access_token(
    user_id: int,
    role: str,
    *,
    expires_delta: timedelta | None = None,
) -> str:
    """生成 access_token。

    payload 包含:
    - sub: str(user_id)
    - role: str
    - type: "access"
    - exp: UTC 过期时间
    - iat: UTC 签发时间
    """
    settings = get_settings()
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.jwt_access_expire_minutes)

    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "role": role,
        "type": "access",
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, _get_secret(), algorithm=_ALGORITHM)


def create_refresh_token(
    user_id: int,
    *,
    expires_delta: timedelta | None = None,
) -> str:
    """生成 refresh_token(只含 user_id,不含 role;刷新时重新查库获取最新 role)。"""
    settings = get_settings()
    if expires_delta is None:
        expires_delta = timedelta(days=settings.jwt_refresh_expire_days)

    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "type": "refresh",
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, _get_secret(), algorithm=_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """解码并验证 JWT 签名 + 过期。

    失败时抛 jwt.PyJWTError(调用方捕获后转 401)。
    """
    return jwt.decode(token, _get_secret(), algorithms=[_ALGORITHM])
