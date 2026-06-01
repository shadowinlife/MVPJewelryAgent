"""Auth 子系统测试:security 工具 + 端点集成。

分两组:
- TestSecurity: 纯单元(密码哈希 + JWT 编解码),不需要 DB / Docker
- TestAuthEndpoints: 集成测试,需要 testcontainers 起 PG

运行:
- 无 Docker: `uv run pytest tests/test_auth.py::TestSecurity -v`
- 有 Docker: `uv run pytest tests/test_auth.py -v`
"""

from __future__ import annotations

from datetime import timedelta

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.deps.db import get_db
from app.main import app as fastapi_app

# ============================================================
# 纯单元测试:core/security.py(无 DB 依赖)
# ============================================================


class TestSecurity:
    """密码哈希 + JWT 令牌的纯函数测试。"""

    def test_hash_and_verify_password(self) -> None:
        """bcrypt 哈希后可正确验证。"""
        plain = "MyP@ss123"
        hashed = hash_password(plain)
        assert hashed != plain
        assert verify_password(plain, hashed)

    def test_verify_wrong_password_fails(self) -> None:
        """错误密码验证返回 False。"""
        hashed = hash_password("correct")
        assert not verify_password("wrong", hashed)

    def test_hash_produces_different_values(self) -> None:
        """同一明文两次哈希产生不同结果(bcrypt 每次生成新 salt)。"""
        h1 = hash_password("same")
        h2 = hash_password("same")
        assert h1 != h2
        assert verify_password("same", h1)
        assert verify_password("same", h2)

    def test_create_access_token_decode(self) -> None:
        """access_token 编码后可解码回 payload。"""
        token = create_access_token(42, "free_user")
        payload = decode_token(token)
        assert payload["sub"] == "42"
        assert payload["role"] == "free_user"
        assert payload["type"] == "access"

    def test_create_refresh_token_decode(self) -> None:
        """refresh_token 编码后可解码回 payload。"""
        token = create_refresh_token(99)
        payload = decode_token(token)
        assert payload["sub"] == "99"
        assert payload["type"] == "refresh"
        assert "role" not in payload

    def test_expired_token_raises(self) -> None:
        """过期令牌解码抛异常。"""
        import jwt as pyjwt

        token = create_access_token(1, "free_user", expires_delta=timedelta(seconds=-1))
        with pytest.raises(pyjwt.ExpiredSignatureError):
            decode_token(token)

    def test_tampered_token_raises(self) -> None:
        """篡改令牌解码抛异常。"""
        import jwt as pyjwt

        token = create_access_token(1, "free_user")
        # 篡改最后一个字符
        tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
        with pytest.raises(pyjwt.InvalidSignatureError):
            decode_token(tampered)


# ============================================================
# 集成测试:Auth endpoints(需要 Docker / testcontainers)
# ============================================================


@pytest_asyncio.fixture
async def db_client(engine: AsyncEngine) -> AsyncClient:
    """带 DB 依赖覆盖的 httpx 客户端。

    把 FastAPI 的 `get_db` 依赖替换为使用 testcontainers 的 session,
    每个测试函数在外层 transaction(SAVEPOINT)内执行,结束后自动回滚。
    """
    async with engine.connect() as conn:
        trans = await conn.begin()
        try:
            session = AsyncSession(
                bind=conn, expire_on_commit=False, join_transaction_mode="create_savepoint"
            )

            async def _override_get_db() -> AsyncSession:  # type: ignore[misc]
                return session

            fastapi_app.dependency_overrides[get_db] = _override_get_db
            transport = ASGITransport(app=fastapi_app)  # type: ignore[arg-type]
            async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
                yield ac  # type: ignore[misc]
            await session.close()
        finally:
            fastapi_app.dependency_overrides.pop(get_db, None)
            if trans.is_active:
                await trans.rollback()


class TestAuthEndpoints:
    """认证端点集成测试(POST register / login / refresh / GET me)。"""

    async def test_register_success(self, db_client: AsyncClient) -> None:
        """注册成功返回令牌对。"""
        resp = await db_client.post(
            "/auth/register",
            json={"phone": "13800000001", "password": "Test123456", "nickname": "张三"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        data = body["data"]
        assert "accessToken" in data
        assert "refreshToken" in data
        assert data["tokenType"] == "Bearer"
        assert data["expiresIn"] > 0

    async def test_register_duplicate_phone(self, db_client: AsyncClient) -> None:
        """重复手机号注册返回 409。"""
        payload = {"phone": "13800000002", "password": "Test123456"}
        await db_client.post("/auth/register", json=payload)
        resp = await db_client.post("/auth/register", json=payload)
        assert resp.status_code == 409
        assert resp.json()["ok"] is False
        assert "已注册" in resp.json()["error"]

    async def test_register_short_password_422(self, db_client: AsyncClient) -> None:
        """密码过短返回 422 校验错误。"""
        resp = await db_client.post(
            "/auth/register", json={"phone": "13800000003", "password": "12345"}
        )
        assert resp.status_code == 422

    async def test_login_success(self, db_client: AsyncClient) -> None:
        """注册后登录成功。"""
        await db_client.post(
            "/auth/register", json={"phone": "13800000010", "password": "Login123"}
        )
        resp = await db_client.post(
            "/auth/login", json={"phone": "13800000010", "password": "Login123"}
        )
        assert resp.status_code == 200
        assert resp.json()["ok"] is True
        assert "accessToken" in resp.json()["data"]

    async def test_login_wrong_password(self, db_client: AsyncClient) -> None:
        """密码错误返回 401。"""
        await db_client.post(
            "/auth/register", json={"phone": "13800000011", "password": "Correct1"}
        )
        resp = await db_client.post(
            "/auth/login", json={"phone": "13800000011", "password": "Wrong1"}
        )
        assert resp.status_code == 401
        assert resp.json()["ok"] is False

    async def test_login_nonexistent_phone(self, db_client: AsyncClient) -> None:
        """不存在的手机号返回 401(不区分"无此号"和"密码错")。"""
        resp = await db_client.post(
            "/auth/login", json={"phone": "19999999999", "password": "Whatever1"}
        )
        assert resp.status_code == 401

    async def test_me_with_valid_token(self, db_client: AsyncClient) -> None:
        """带有效 token 访问 /auth/me 返回用户信息。"""
        reg = await db_client.post(
            "/auth/register", json={"phone": "13800000020", "password": "Me12345", "nickname": "测试"}
        )
        token = reg.json()["data"]["accessToken"]
        resp = await db_client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["phone"] == "13800000020"
        assert data["nickname"] == "测试"
        assert data["role"] == "free_user"

    async def test_me_without_token_401(self, db_client: AsyncClient) -> None:
        """无 token 访问 /auth/me 返回 401。"""
        resp = await db_client.get("/auth/me")
        assert resp.status_code == 401

    async def test_me_with_invalid_token_401(self, db_client: AsyncClient) -> None:
        """无效 token 访问 /auth/me 返回 401。"""
        resp = await db_client.get(
            "/auth/me", headers={"Authorization": "Bearer invalid.token.here"}
        )
        assert resp.status_code == 401

    async def test_refresh_token_success(self, db_client: AsyncClient) -> None:
        """用 refresh_token 换发新令牌对。"""
        reg = await db_client.post(
            "/auth/register", json={"phone": "13800000030", "password": "Refresh1"}
        )
        refresh_token = reg.json()["data"]["refreshToken"]
        resp = await db_client.post(
            "/auth/refresh", json={"refreshToken": refresh_token}
        )
        assert resp.status_code == 200
        assert resp.json()["ok"] is True
        assert "accessToken" in resp.json()["data"]

    async def test_refresh_with_access_token_fails(self, db_client: AsyncClient) -> None:
        """用 access_token 当 refresh_token 使用应失败。"""
        reg = await db_client.post(
            "/auth/register", json={"phone": "13800000031", "password": "Refresh2"}
        )
        access_token = reg.json()["data"]["accessToken"]
        resp = await db_client.post(
            "/auth/refresh", json={"refreshToken": access_token}
        )
        assert resp.status_code == 401

    async def test_refresh_with_expired_token_fails(self, db_client: AsyncClient) -> None:
        """过期的 refresh_token 应返回 401。"""
        expired_token = create_refresh_token(9999, expires_delta=timedelta(seconds=-1))
        resp = await db_client.post(
            "/auth/refresh", json={"refreshToken": expired_token}
        )
        assert resp.status_code == 401
