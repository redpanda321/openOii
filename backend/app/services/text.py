from __future__ import annotations

import asyncio
import json
import logging
import random
from typing import Any, AsyncIterator

import httpx

from app.config import Settings

logger = logging.getLogger(__name__)


# 导入 LLMResponse 以保持接口兼容
from app.services.llm import LLMResponse


class TextServiceError(Exception):
    """文本服务基础异常"""

    def __init__(self, message: str, status_code: int | None = None, response_body: str | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class TextServiceAuthError(TextServiceError):
    """认证失败异常（401/403）"""


class TextServiceRateLimitError(TextServiceError):
    """限流异常（429）"""


class TextServiceServerError(TextServiceError):
    """服务器错误异常（5xx）"""


class TextService:
    """文本生成服务（OpenAI 兼容接口，支持流式与非流式输出）"""

    def __init__(self, settings: Settings, *, max_retries: int = 3):
        self.settings = settings
        self.max_retries = max_retries

    def _build_url(self) -> str:
        base = self.settings.text_base_url.rstrip("/")
        endpoint = self.settings.text_endpoint
        if not endpoint.startswith("/"):
            endpoint = "/" + endpoint
        return f"{base}{endpoint}"

    def _is_retryable_status(self, status_code: int) -> bool:
        return status_code in {408, 429, 500, 502, 503, 504}

    def _is_chat_endpoint(self) -> bool:
        return "/chat/completions" in self.settings.text_endpoint

    async def _post_json_with_retry(self, url: str, payload: dict[str, Any]) -> dict[str, Any]:
        last_exc: Exception | None = None
        last_status: int | None = None
        last_body: str | None = None

        async with httpx.AsyncClient(timeout=self.settings.request_timeout_s) as client:
            for attempt in range(self.max_retries + 1):
                try:
                    res = await client.post(url, headers=self.settings.text_headers(), json=payload)
                    res.raise_for_status()
                    return res.json()

                except httpx.HTTPStatusError as exc:
                    last_exc = exc
                    last_status = exc.response.status_code
                    try:
                        last_body = exc.response.text[:500]
                    except Exception:
                        last_body = None

                    if attempt >= self.max_retries or not self._is_retryable_status(last_status):
                        break

                    await asyncio.sleep(0.5 * (2**attempt))

                except (httpx.TimeoutException, httpx.NetworkError) as exc:
                    last_exc = exc
                    if attempt >= self.max_retries:
                        break
                    await asyncio.sleep(0.5 * (2**attempt))

        # 根据状态码抛出不同的异常
        if last_status in (401, 403):
            raise TextServiceAuthError(
                f"Authentication failed (HTTP {last_status})",
                status_code=last_status,
                response_body=last_body,
            ) from last_exc
        elif last_status == 429:
            raise TextServiceRateLimitError(
                f"Rate limit exceeded (HTTP {last_status})",
                status_code=last_status,
                response_body=last_body,
            ) from last_exc
        elif last_status and last_status >= 500:
            raise TextServiceServerError(
                f"Server error (HTTP {last_status})",
                status_code=last_status,
                response_body=last_body,
            ) from last_exc
        else:
            raise TextServiceError(
                f"Text generation request failed after {self.max_retries} retries",
                status_code=last_status,
                response_body=last_body,
            ) from last_exc

    async def _post_stream_with_retry(self, url: str, payload: dict[str, Any]) -> AsyncIterator[dict[str, Any]]:
        delay_s = 0.5
        last_exc: Exception | None = None
        last_status: int | None = None
        last_body: str | None = None

        timeout = httpx.Timeout(self.settings.request_timeout_s, connect=30.0)

        async with httpx.AsyncClient(timeout=timeout) as client:
            for attempt in range(self.max_retries + 1):
                emitted_any = False
                try:
                    async with client.stream(
                        "POST", url, headers=self.settings.text_headers(), json=payload
                    ) as res:
                        last_status = res.status_code

                        if self._is_retryable_status(res.status_code) and attempt < self.max_retries:
                            # 检查 Retry-After 头
                            retry_after = res.headers.get("Retry-After")
                            if retry_after:
                                try:
                                    wait_time = float(retry_after)
                                    delay_s = min(wait_time, 60.0)
                                except ValueError:
                                    pass

                            jitter = delay_s * 0.2 * (2 * random.random() - 1)
                            await asyncio.sleep(delay_s + jitter)
                            delay_s = min(delay_s * 2, 30.0)
                            continue

                        res.raise_for_status()

                        async for line in res.aiter_lines():
                            if not line or not line.startswith("data: "):
                                continue
                            data_str = line[6:]
                            if data_str.strip() == "[DONE]":
                                break
                            try:
                                chunk = json.loads(data_str)
                            except json.JSONDecodeError as exc:
                                logger.debug("Skipping non-JSON line in text stream: %s", exc)
                                continue

                            if "error" in chunk:
                                raise TextServiceError(f"Stream error: {chunk['error']}")

                            emitted_any = True
                            yield chunk

                    return

                except httpx.HTTPStatusError as exc:
                    last_exc = exc
                    last_status = exc.response.status_code
                    try:
                        last_body = exc.response.text[:500]
                    except Exception:
                        last_body = None

                    if emitted_any:
                        break
                    if attempt >= self.max_retries:
                        break
                    if not self._is_retryable_status(last_status):
                        break

                    jitter = delay_s * 0.2 * (2 * random.random() - 1)
                    await asyncio.sleep(delay_s + jitter)
                    delay_s = min(delay_s * 2, 30.0)

                except (httpx.TimeoutException, httpx.NetworkError) as exc:
                    last_exc = exc
                    if emitted_any:
                        break
                    if attempt >= self.max_retries:
                        break

                    jitter = delay_s * 0.2 * (2 * random.random() - 1)
                    await asyncio.sleep(delay_s + jitter)
                    delay_s = min(delay_s * 2, 30.0)

        # 根据状态码抛出不同的异常
        if last_status == 401 or last_status == 403:
            raise TextServiceAuthError(
                f"Authentication failed (HTTP {last_status})",
                status_code=last_status,
                response_body=last_body,
            ) from last_exc
        elif last_status == 429:
            raise TextServiceRateLimitError(
                f"Rate limit exceeded (HTTP {last_status})",
                status_code=last_status,
                response_body=last_body,
            ) from last_exc
        elif last_status and last_status >= 500:
            raise TextServiceServerError(
                f"Server error (HTTP {last_status})",
                status_code=last_status,
                response_body=last_body,
            ) from last_exc
        else:
            raise TextServiceError(
                f"Text generation stream failed after {self.max_retries} retries",
                status_code=last_status,
                response_body=last_body,
            ) from last_exc

    def _extract_text_from_response(self, data: dict[str, Any]) -> str:
        choices = data.get("choices", [])
        if not isinstance(choices, list) or not choices:
            raise RuntimeError(f"Text API response missing choices: {data}")

        first = choices[0] if isinstance(choices[0], dict) else {}
        if self._is_chat_endpoint():
            message = first.get("message", {})
            if isinstance(message, dict):
                content = message.get("content")
                if isinstance(content, str):
                    return content
            raise RuntimeError(f"Text chat response missing message.content: {data}")

        text = first.get("text")
        if isinstance(text, str):
            return text
        raise RuntimeError(f"Text completions response missing choices[0].text: {data}")

    def _extract_text_from_stream_chunk(self, chunk: dict[str, Any]) -> str:
        choices = chunk.get("choices", [])
        if not isinstance(choices, list) or not choices:
            return ""

        first = choices[0] if isinstance(choices[0], dict) else {}
        if self._is_chat_endpoint():
            delta = first.get("delta", {})
            if isinstance(delta, dict):
                content = delta.get("content")
                if isinstance(content, str):
                    return content
            return ""

        text = first.get("text")
        return text if isinstance(text, str) else ""

    async def generate(
        self,
        *,
        messages: list[dict[str, Any]] | None = None,
        prompt: str | None = None,
        system: str | None = None,
        max_tokens: int = 1024,
        temperature: float | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """生成文本（兼容 LLMService 接口）

        Args:
            messages: 消息列表（优先使用）
            prompt: 提示词（向后兼容）
            system: 系统提示（可选）
            max_tokens: 最大 token 数
            temperature: 温度参数
            **kwargs: 其他参数

        Returns:
            LLMResponse 对象（与 LLMService 兼容）
        """
        url = self._build_url()

        payload: dict[str, Any] = {
            "model": self.settings.text_model,
            "max_tokens": max_tokens,
            **kwargs,
        }
        if temperature is not None:
            payload["temperature"] = temperature

        if self._is_chat_endpoint():
            # Chat 端点使用 messages
            if messages:
                payload["messages"] = messages
                # 如果有 system，添加到 messages 开头
                if system:
                    payload["messages"] = [{"role": "system", "content": system}] + payload["messages"]
            elif prompt:
                payload["messages"] = [{"role": "user", "content": prompt}]
                if system:
                    payload["messages"] = [{"role": "system", "content": system}] + payload["messages"]
            else:
                raise ValueError("Either messages or prompt must be provided")
        else:
            # Completions 端点使用 prompt
            if messages:
                # 将 messages 转换为 prompt
                prompt_parts = []
                if system:
                    prompt_parts.append(f"System: {system}")
                for msg in messages:
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    prompt_parts.append(f"{role.capitalize()}: {content}")
                payload["prompt"] = "\n\n".join(prompt_parts)
            elif prompt:
                if system:
                    payload["prompt"] = f"System: {system}\n\n{prompt}"
                else:
                    payload["prompt"] = prompt
            else:
                raise ValueError("Either messages or prompt must be provided")

        payload["stream"] = False

        data = await self._post_json_with_retry(url, payload)
        text = self._extract_text_from_response(data)
        return LLMResponse(text=text, tool_calls=[], raw=data)

    async def stream(
        self,
        *,
        messages: list[dict[str, Any]] | None = None,
        prompt: str | None = None,
        system: str | None = None,
        max_tokens: int = 1024,
        temperature: float | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[dict[str, Any]]:
        """流式生成文本（兼容 LLMService 接口）

        Args:
            messages: 消息列表（优先使用）
            prompt: 提示词（向后兼容）
            system: 系统提示（可选）
            max_tokens: 最大 token 数
            temperature: 温度参数
            **kwargs: 其他参数

        Yields:
            事件字典（与 LLMService 兼容）:
            - {"type": "text", "text": "..."}  # 增量文本
            - {"type": "final", "response": LLMResponse(...)}  # 最终响应
        """
        url = self._build_url()

        payload: dict[str, Any] = {
            "model": self.settings.text_model,
            "max_tokens": max_tokens,
            **kwargs,
        }
        if temperature is not None:
            payload["temperature"] = temperature

        if self._is_chat_endpoint():
            # Chat 端点使用 messages
            if messages:
                payload["messages"] = messages
                # 如果有 system，添加到 messages 开头
                if system:
                    payload["messages"] = [{"role": "system", "content": system}] + payload["messages"]
            elif prompt:
                payload["messages"] = [{"role": "user", "content": prompt}]
                if system:
                    payload["messages"] = [{"role": "system", "content": system}] + payload["messages"]
            else:
                raise ValueError("Either messages or prompt must be provided")
        else:
            # Completions 端点使用 prompt
            if messages:
                # 将 messages 转换为 prompt
                prompt_parts = []
                if system:
                    prompt_parts.append(f"System: {system}")
                for msg in messages:
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    prompt_parts.append(f"{role.capitalize()}: {content}")
                payload["prompt"] = "\n\n".join(prompt_parts)
            elif prompt:
                if system:
                    payload["prompt"] = f"System: {system}\n\n{prompt}"
                else:
                    payload["prompt"] = prompt
            else:
                raise ValueError("Either messages or prompt must be provided")

        payload["stream"] = True

        # 收集完整文本用于最终响应
        full_text = []

        async for chunk in self._post_stream_with_retry(url, payload):
            text = self._extract_text_from_stream_chunk(chunk)
            if text:
                full_text.append(text)
                # 产出增量文本事件
                yield {"type": "text", "text": text}

        # 产出最终响应事件
        complete_text = "".join(full_text)
        yield {
            "type": "final",
            "response": LLMResponse(text=complete_text, tool_calls=[], raw=None)
        }
