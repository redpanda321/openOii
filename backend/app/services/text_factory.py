from __future__ import annotations

from typing import Protocol

from app.config import Settings
from app.services.llm import LLMService
from app.services.text import TextService


class TextServiceProtocol(Protocol):
    """文本生成服务协议（LLM 或 OpenAI 兼容）"""

    async def generate(self, *, prompt: str, max_tokens: int = 1024, **kwargs) -> str:
        ...


def create_text_service(settings: Settings) -> TextServiceProtocol:
    """根据配置创建文本生成服务

    Args:
        settings: 应用配置

    Returns:
        LLMService（Anthropic）或 TextService（OpenAI 兼容）
    """
    if settings.text_provider == "openai":
        return TextService(settings)
    else:
        # 默认使用 Anthropic
        return LLMService(settings)
