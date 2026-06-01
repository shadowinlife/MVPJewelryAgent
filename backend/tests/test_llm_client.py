"""LLMClient Protocol 一致性 + 加密工具 + Provider 适配器单元测试。"""

from __future__ import annotations

import pytest
from cryptography.fernet import InvalidToken

from app.integrations.ai.azure_openai_client import AzureOpenAILLMClient
from app.integrations.ai.client import LLMClient
from app.integrations.ai.dashscope_client import DashScopeLLMClient
from app.integrations.ai.encryption import decrypt_value, encrypt_value, mask_key

# ============================================================
# Protocol 一致性
# ============================================================


class TestProtocolConformance:
    """验证两个适配器都满足 LLMClient Protocol。"""

    def test_dashscope_client_is_llm_client(self) -> None:
        """DashScopeLLMClient 结构满足 LLMClient Protocol。"""
        client = DashScopeLLMClient(
            api_key="sk-test", endpoint="https://example.com/v1", model_name="qwen-max"
        )
        assert isinstance(client, LLMClient)

    def test_azure_openai_client_is_llm_client(self) -> None:
        """AzureOpenAILLMClient 结构满足 LLMClient Protocol。"""
        client = AzureOpenAILLMClient(
            api_key="test-key",
            endpoint="https://example.openai.azure.com/",
            model_name="gpt-4o-mini",
        )
        assert isinstance(client, LLMClient)


# ============================================================
# 加密工具
# ============================================================


class TestEncryption:
    """Fernet 加密/解密 + 脱敏测试。"""

    def test_encrypt_decrypt_roundtrip(self) -> None:
        """加密后解密应还原原文。"""
        original = "sk-abc123456789xyz"
        ciphertext = encrypt_value(original)
        # 密文不等于明文
        assert ciphertext != original
        # 解密还原
        assert decrypt_value(ciphertext) == original

    def test_encrypt_produces_different_ciphertext(self) -> None:
        """同一明文两次加密产生不同密文(Fernet 含时间戳+随机 IV)。"""
        original = "sk-test-key-12345"
        c1 = encrypt_value(original)
        c2 = encrypt_value(original)
        assert c1 != c2
        # 但都能解密回原文
        assert decrypt_value(c1) == original
        assert decrypt_value(c2) == original

    def test_mask_key_short(self) -> None:
        """短于 4 字符的 key 全部遮盖。"""
        assert mask_key("abc") == "****"
        assert mask_key("") == "****"

    def test_mask_key_normal(self) -> None:
        """正常长度 key 只露后 4 位。"""
        assert mask_key("sk-abc123456789") == "****6789"
        assert mask_key("12345678") == "****5678"

    def test_decrypt_invalid_raises(self) -> None:
        """无效密文应抛 InvalidToken。"""
        with pytest.raises(InvalidToken):
            decrypt_value("not-a-valid-ciphertext")
