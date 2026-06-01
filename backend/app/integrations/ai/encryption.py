"""API Key 加密/解密工具 — 基于 Fernet 对称加密。

用途:LLM Provider 的 API Key 存入数据库前加密,读取时解密。
加密密钥来自环境变量 `LLM_CONFIG_ENCRYPTION_KEY`(Fernet base64 格式)。

生成密钥:
    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
"""

from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import get_settings


def _get_fernet() -> Fernet:
    """从 Settings 获取加密密钥并构造 Fernet 实例。

    若 `llm_config_encryption_key` 为空,使用 `jwt_secret` 派生
    (仅限本地开发,不推荐 production 使用)。
    """
    settings = get_settings()
    key = settings.llm_config_encryption_key
    if not key:
        # 降级:从 jwt_secret 派生 — 仅 local 环境可接受
        import base64
        import hashlib

        raw = settings.jwt_secret or "dev-fallback-key-not-for-prod"
        derived = base64.urlsafe_b64encode(
            hashlib.sha256(raw.encode()).digest()
        )
        return Fernet(derived)
    return Fernet(key.encode())


def encrypt_value(plaintext: str) -> str:
    """加密明文,返回 base64 密文字符串(可直接存数据库)。"""
    f = _get_fernet()
    return f.encrypt(plaintext.encode()).decode()


def decrypt_value(ciphertext: str) -> str:
    """解密密文,返回原始明文。

    Raises:
        InvalidToken: 密文被篡改或密钥不匹配。
    """
    f = _get_fernet()
    return f.decrypt(ciphertext.encode()).decode()


def mask_key(plaintext: str) -> str:
    """将 API Key 脱敏为 `sk-****xxxx` 格式(只露后 4 位)。"""
    if len(plaintext) <= 4:
        return "****"
    return f"{'*' * 4}{plaintext[-4:]}"


__all__ = ["decrypt_value", "encrypt_value", "mask_key", "InvalidToken"]
