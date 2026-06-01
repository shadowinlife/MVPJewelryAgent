"""认证相关 Pydantic Schema。

- RegisterRequest / LoginRequest: 前端请求体
- TokenResponse: 登录/刷新成功后返回的令牌对
- RefreshRequest: 刷新令牌请求体
- UserRead: 当前用户信息(GET /auth/me 响应)
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class RegisterRequest(BaseModel):
    """注册请求体(MVP 阶段:手机号 + 密码)。"""

    model_config = ConfigDict(extra="forbid")

    phone: str = Field(min_length=11, max_length=20, description="手机号")
    password: str = Field(min_length=6, max_length=128, description="密码(明文,后端做哈希)")
    nickname: str | None = Field(default=None, max_length=64, description="昵称(可选)")


class LoginRequest(BaseModel):
    """登录请求体。"""

    model_config = ConfigDict(extra="forbid")

    phone: str = Field(min_length=11, max_length=20, description="手机号")
    password: str = Field(min_length=1, max_length=128, description="密码")


class RefreshRequest(BaseModel):
    """刷新令牌请求体。

    前端发 camelCase(`refreshToken`),后端用 snake_case(`refresh_token`)。
    """

    model_config = ConfigDict(
        extra="forbid",
        alias_generator=to_camel,
        populate_by_name=True,
    )

    refresh_token: str


class TokenResponse(BaseModel):
    """登录 / 刷新成功后的令牌响应。

    camelCase 输出(对齐前端 TypeScript 契约)。
    """

    model_config = ConfigDict(
        extra="forbid",
        alias_generator=to_camel,
        populate_by_name=True,
    )

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = Field(description="access_token 有效秒数")


class UserRead(BaseModel):
    """当前用户信息(GET /auth/me 响应)。

    camelCase 输出;只暴露前端需要的字段,不泄漏 password_hash / 内部 ID 策略。
    """

    model_config = ConfigDict(
        extra="forbid",
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    id: int
    phone: str
    nickname: str | None
    avatar_url: str | None
    role: str
    status: str
    last_login_at: datetime | None
    created_at: datetime
