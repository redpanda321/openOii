from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any, AsyncIterator

from app.config import Settings


@dataclass(slots=True)
class ToolCall:
    id: str
    name: str
    input: dict[str, Any]


@dataclass(slots=True)
class LLMResponse:
    text: str
    tool_calls: list[ToolCall]
    raw: Any


class LLMService:
    """Multi-provider LLM service wrapper.

    Supports:
    - ``anthropic`` — native Anthropic Messages API
    - ``openai`` / ``openai-compatible`` — OpenAI Chat Completions API
      (works with new-api gateway, Azure, etc.)

    The public interface (``generate`` / ``stream``) returns the same
    ``LLMResponse`` regardless of provider.
    """

    def __init__(self, settings: Settings, *, max_retries: int = 3):
        self.settings = settings
        self.max_retries = max_retries
        self._anthropic_client: Any | None = None
        self._openai_client: Any | None = None
        self._anthropic_mod: Any | None = None
        self._openai_mod: Any | None = None

    @property
    def _provider(self) -> str:
        return self.settings.effective_llm_provider

    @property
    def _model(self) -> str:
        return self.settings.effective_llm_model

    # ------------------------------------------------------------------
    # Anthropic helpers
    # ------------------------------------------------------------------

    def _import_anthropic(self) -> Any:
        if self._anthropic_mod is not None:
            return self._anthropic_mod
        try:
            import anthropic  # type: ignore
        except ModuleNotFoundError as exc:  # pragma: no cover
            raise RuntimeError(
                "Missing dependency `anthropic`. Install optional deps: `uv sync --extra agents` "
                "or `pip install 'hanggent-comic-backend[agents]'`."
            ) from exc
        self._anthropic_mod = anthropic
        return anthropic

    def _get_anthropic_client(self) -> Any:
        if self._anthropic_client is not None:
            return self._anthropic_client

        anthropic = self._import_anthropic()

        api_key = self.settings.effective_llm_api_key or self.settings.anthropic_auth_token
        if not api_key:
            raise ValueError("Anthropic credentials missing: set `llm_api_key` / `anthropic_api_key` or `anthropic_auth_token`.")

        default_headers: dict[str, str] = {}
        if self.settings.anthropic_auth_token:
            default_headers["Authorization"] = f"Bearer {self.settings.anthropic_auth_token}"

        kwargs: dict[str, Any] = {
            "api_key": api_key,
            "timeout": self.settings.request_timeout_s,
            "max_retries": 0,
        }
        base_url = self.settings.effective_llm_base_url
        if base_url:
            kwargs["base_url"] = base_url
        if default_headers:
            kwargs["default_headers"] = default_headers

        self._anthropic_client = anthropic.AsyncAnthropic(**kwargs)
        return self._anthropic_client

    def _parse_anthropic_message(self, message: Any) -> LLMResponse:
        text_parts: list[str] = []
        tool_calls: list[ToolCall] = []

        for block in getattr(message, "content", []) or []:
            block_type = getattr(block, "type", None)
            if block_type == "text":
                text_parts.append(getattr(block, "text", ""))
            elif block_type == "tool_use":
                tool_calls.append(
                    ToolCall(
                        id=str(getattr(block, "id", "")),
                        name=str(getattr(block, "name", "")),
                        input=dict(getattr(block, "input", {}) or {}),
                    )
                )

        return LLMResponse(text="".join(text_parts), tool_calls=tool_calls, raw=message)

    def _is_retryable_anthropic_error(self, exc: Exception) -> bool:
        anthropic = self._import_anthropic()
        retryable_types: tuple[type[BaseException], ...] = (
            getattr(anthropic, "RateLimitError", Exception),
            getattr(anthropic, "APIConnectionError", Exception),
            getattr(anthropic, "APITimeoutError", Exception),
        )
        if isinstance(exc, retryable_types):
            return True

        status_code = getattr(exc, "status_code", None)
        if isinstance(status_code, int) and status_code in {408, 429, 500, 502, 503, 504}:
            return True

        return False

    # ------------------------------------------------------------------
    # OpenAI / OpenAI-compatible helpers
    # ------------------------------------------------------------------

    def _import_openai(self) -> Any:
        if self._openai_mod is not None:
            return self._openai_mod
        try:
            import openai  # type: ignore
        except ModuleNotFoundError as exc:  # pragma: no cover
            raise RuntimeError(
                "Missing dependency `openai`. Install optional deps: `uv sync --extra agents` "
                "or `pip install 'hanggent-comic-backend[agents]'`."
            ) from exc
        self._openai_mod = openai
        return openai

    def _get_openai_client(self) -> Any:
        if self._openai_client is not None:
            return self._openai_client

        openai = self._import_openai()

        api_key = self.settings.effective_llm_api_key
        if not api_key:
            raise ValueError("OpenAI credentials missing: set `llm_api_key`.")

        kwargs: dict[str, Any] = {
            "api_key": api_key,
            "timeout": self.settings.request_timeout_s,
            "max_retries": 0,
        }
        base_url = self.settings.effective_llm_base_url
        if base_url:
            kwargs["base_url"] = base_url

        self._openai_client = openai.AsyncOpenAI(**kwargs)
        return self._openai_client

    @staticmethod
    def _translate_tools_to_openai(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Convert Anthropic-style tool definitions to OpenAI function-calling format."""
        result: list[dict[str, Any]] = []
        for tool in tools:
            result.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("input_schema", {}),
                },
            })
        return result

    @staticmethod
    def _translate_tool_choice_to_openai(tool_choice: dict[str, Any]) -> Any:
        """Convert Anthropic tool_choice to OpenAI format."""
        tc_type = tool_choice.get("type", "auto")
        if tc_type == "any":
            return "required"
        if tc_type == "tool":
            return {"type": "function", "function": {"name": tool_choice["name"]}}
        return "auto"

    @staticmethod
    def _translate_messages_to_openai(
        messages: list[dict[str, Any]],
        system: str | None = None,
    ) -> list[dict[str, Any]]:
        """Convert Anthropic-style messages to OpenAI format.

        Handles system prompt injection and tool_result → tool role conversion.
        """
        oai_messages: list[dict[str, Any]] = []
        if system:
            oai_messages.append({"role": "system", "content": system})

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content")

            # Anthropic tool_result blocks → OpenAI tool role messages
            if isinstance(content, list):
                # Check if all blocks are tool_result
                tool_results = [b for b in content if isinstance(b, dict) and b.get("type") == "tool_result"]
                if tool_results:
                    for block in tool_results:
                        result_content = block.get("content", "")
                        if isinstance(result_content, list):
                            result_content = " ".join(
                                b.get("text", "") for b in result_content if isinstance(b, dict)
                            )
                        oai_messages.append({
                            "role": "tool",
                            "tool_call_id": block.get("tool_use_id", ""),
                            "content": str(result_content),
                        })
                    continue

                # Mixed content blocks → join text parts
                text_parts = []
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        text_parts.append(block.get("text", ""))
                if text_parts:
                    oai_messages.append({"role": role, "content": "".join(text_parts)})
                    continue

            # Anthropic assistant messages with tool_use → OpenAI tool_calls
            if role == "assistant" and isinstance(content, list):
                text_parts = []
                tool_calls_list = []
                for block in content:
                    if isinstance(block, dict):
                        if block.get("type") == "text":
                            text_parts.append(block.get("text", ""))
                        elif block.get("type") == "tool_use":
                            tool_calls_list.append({
                                "id": block.get("id", ""),
                                "type": "function",
                                "function": {
                                    "name": block.get("name", ""),
                                    "arguments": json.dumps(block.get("input", {})),
                                },
                            })
                oai_msg: dict[str, Any] = {"role": "assistant"}
                if text_parts:
                    oai_msg["content"] = "".join(text_parts)
                if tool_calls_list:
                    oai_msg["tool_calls"] = tool_calls_list
                oai_messages.append(oai_msg)
                continue

            # Simple string content
            oai_messages.append({"role": role, "content": content})

        return oai_messages

    def _parse_openai_message(self, choice: Any) -> LLMResponse:
        message = getattr(choice, "message", choice)
        text = getattr(message, "content", None) or ""
        tool_calls: list[ToolCall] = []

        for tc in getattr(message, "tool_calls", None) or []:
            fn = getattr(tc, "function", None)
            if fn is None:
                continue
            try:
                args = json.loads(getattr(fn, "arguments", "{}") or "{}")
            except (json.JSONDecodeError, TypeError):
                args = {}
            tool_calls.append(
                ToolCall(
                    id=str(getattr(tc, "id", "")),
                    name=str(getattr(fn, "name", "")),
                    input=args,
                )
            )

        return LLMResponse(text=text, tool_calls=tool_calls, raw=message)

    def _is_retryable_openai_error(self, exc: Exception) -> bool:
        openai = self._import_openai()
        retryable_types: tuple[type[BaseException], ...] = (
            getattr(openai, "RateLimitError", Exception),
            getattr(openai, "APIConnectionError", Exception),
            getattr(openai, "APITimeoutError", Exception),
        )
        if isinstance(exc, retryable_types):
            return True

        status_code = getattr(exc, "status_code", None)
        if isinstance(status_code, int) and status_code in {408, 429, 500, 502, 503, 504}:
            return True

        return False

    # ------------------------------------------------------------------
    # Unified retry helper
    # ------------------------------------------------------------------

    def _is_retryable_error(self, exc: Exception) -> bool:
        if self._provider == "anthropic":
            return self._is_retryable_anthropic_error(exc)
        return self._is_retryable_openai_error(exc)

    # ------------------------------------------------------------------
    # Public API — generate (non-streaming)
    # ------------------------------------------------------------------

    async def generate(
        self,
        *,
        messages: list[dict[str, Any]],
        system: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: dict[str, Any] | None = None,
        model: str | None = None,
        max_tokens: int = 1024,
        temperature: float | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        if self._provider == "anthropic":
            return await self._generate_anthropic(
                messages=messages, system=system, tools=tools,
                tool_choice=tool_choice, model=model,
                max_tokens=max_tokens, temperature=temperature, **kwargs,
            )
        return await self._generate_openai(
            messages=messages, system=system, tools=tools,
            tool_choice=tool_choice, model=model,
            max_tokens=max_tokens, temperature=temperature, **kwargs,
        )

    async def _generate_anthropic(
        self,
        *,
        messages: list[dict[str, Any]],
        system: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: dict[str, Any] | None = None,
        model: str | None = None,
        max_tokens: int = 1024,
        temperature: float | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        client = self._get_anthropic_client()

        payload: dict[str, Any] = {
            "model": model or self._model,
            "max_tokens": max_tokens,
            "messages": messages,
            **kwargs,
        }
        if system is not None:
            payload["system"] = system
        if tools is not None:
            payload["tools"] = tools
        if tool_choice is not None:
            payload["tool_choice"] = tool_choice
        if temperature is not None:
            payload["temperature"] = temperature

        delay_s = 0.5
        for attempt in range(self.max_retries + 1):
            try:
                message = await client.messages.create(**payload)
                return self._parse_anthropic_message(message)
            except Exception as exc:
                if attempt >= self.max_retries or not self._is_retryable_error(exc):
                    raise
                await asyncio.sleep(delay_s)
                delay_s = min(delay_s * 2, 8.0)

        raise RuntimeError("unreachable")  # pragma: no cover

    async def _generate_openai(
        self,
        *,
        messages: list[dict[str, Any]],
        system: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: dict[str, Any] | None = None,
        model: str | None = None,
        max_tokens: int = 1024,
        temperature: float | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        client = self._get_openai_client()
        oai_messages = self._translate_messages_to_openai(messages, system)

        payload: dict[str, Any] = {
            "model": model or self._model,
            "max_tokens": max_tokens,
            "messages": oai_messages,
        }
        if tools:
            payload["tools"] = self._translate_tools_to_openai(tools)
        if tool_choice is not None:
            payload["tool_choice"] = self._translate_tool_choice_to_openai(tool_choice)
        if temperature is not None:
            payload["temperature"] = temperature

        delay_s = 0.5
        for attempt in range(self.max_retries + 1):
            try:
                response = await client.chat.completions.create(**payload)
                return self._parse_openai_message(response.choices[0])
            except Exception as exc:
                if attempt >= self.max_retries or not self._is_retryable_error(exc):
                    raise
                await asyncio.sleep(delay_s)
                delay_s = min(delay_s * 2, 8.0)

        raise RuntimeError("unreachable")  # pragma: no cover

    # ------------------------------------------------------------------
    # Public API — stream
    # ------------------------------------------------------------------

    async def stream(
        self,
        *,
        messages: list[dict[str, Any]],
        system: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: dict[str, Any] | None = None,
        model: str | None = None,
        max_tokens: int = 1024,
        temperature: float | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[dict[str, Any]]:
        """Streaming output.

        Yields events:
        - {"type": "text", "text": "..."}  — incremental text
        - {"type": "final", "response": LLMResponse(...)}  — final aggregated result
        """
        if self._provider == "anthropic":
            async for event in self._stream_anthropic(
                messages=messages, system=system, tools=tools,
                tool_choice=tool_choice, model=model,
                max_tokens=max_tokens, temperature=temperature, **kwargs,
            ):
                yield event
        else:
            async for event in self._stream_openai(
                messages=messages, system=system, tools=tools,
                tool_choice=tool_choice, model=model,
                max_tokens=max_tokens, temperature=temperature, **kwargs,
            ):
                yield event

    async def _stream_anthropic(
        self,
        *,
        messages: list[dict[str, Any]],
        system: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: dict[str, Any] | None = None,
        model: str | None = None,
        max_tokens: int = 1024,
        temperature: float | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[dict[str, Any]]:
        client = self._get_anthropic_client()

        payload: dict[str, Any] = {
            "model": model or self._model,
            "max_tokens": max_tokens,
            "messages": messages,
            **kwargs,
        }
        if system is not None:
            payload["system"] = system
        if tools is not None:
            payload["tools"] = tools
        if tool_choice is not None:
            payload["tool_choice"] = tool_choice
        if temperature is not None:
            payload["temperature"] = temperature

        delay_s = 0.5
        for attempt in range(self.max_retries + 1):
            try:
                async with client.messages.stream(**payload) as stream:
                    text_stream = getattr(stream, "text_stream", None)
                    if text_stream is not None:
                        async for text in text_stream:
                            yield {"type": "text", "text": text}
                    else:  # pragma: no cover
                        async for event in stream:
                            event_type = getattr(event, "type", None)
                            if event_type == "text":
                                yield {"type": "text", "text": getattr(event, "text", "")}
                            elif event_type == "content_block_delta":
                                delta = getattr(event, "delta", None)
                                delta_text = getattr(delta, "text", None)
                                if isinstance(delta_text, str):
                                    yield {"type": "text", "text": delta_text}

                    final_message = await stream.get_final_message()
                    yield {"type": "final", "response": self._parse_anthropic_message(final_message)}
                return
            except Exception as exc:
                if attempt >= self.max_retries or not self._is_retryable_error(exc):
                    raise
                await asyncio.sleep(delay_s)
                delay_s = min(delay_s * 2, 8.0)

        raise RuntimeError("unreachable")  # pragma: no cover

    async def _stream_openai(
        self,
        *,
        messages: list[dict[str, Any]],
        system: str | None = None,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: dict[str, Any] | None = None,
        model: str | None = None,
        max_tokens: int = 1024,
        temperature: float | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[dict[str, Any]]:
        client = self._get_openai_client()
        oai_messages = self._translate_messages_to_openai(messages, system)

        payload: dict[str, Any] = {
            "model": model or self._model,
            "max_tokens": max_tokens,
            "messages": oai_messages,
            "stream": True,
        }
        if tools:
            payload["tools"] = self._translate_tools_to_openai(tools)
        if tool_choice is not None:
            payload["tool_choice"] = self._translate_tool_choice_to_openai(tool_choice)
        if temperature is not None:
            payload["temperature"] = temperature

        delay_s = 0.5
        for attempt in range(self.max_retries + 1):
            try:
                accumulated_text = ""
                accumulated_tool_calls: dict[int, dict[str, Any]] = {}

                response_stream = await client.chat.completions.create(**payload)
                async for chunk in response_stream:
                    if not chunk.choices:
                        continue
                    delta = chunk.choices[0].delta

                    # Text content
                    if delta.content:
                        accumulated_text += delta.content
                        yield {"type": "text", "text": delta.content}

                    # Tool call deltas
                    for tc_delta in delta.tool_calls or []:
                        idx = tc_delta.index
                        if idx not in accumulated_tool_calls:
                            accumulated_tool_calls[idx] = {
                                "id": getattr(tc_delta, "id", "") or "",
                                "name": "",
                                "arguments": "",
                            }
                        entry = accumulated_tool_calls[idx]
                        if tc_delta.id:
                            entry["id"] = tc_delta.id
                        fn = getattr(tc_delta, "function", None)
                        if fn:
                            if fn.name:
                                entry["name"] = fn.name
                            if fn.arguments:
                                entry["arguments"] += fn.arguments

                # Build final LLMResponse
                tool_calls: list[ToolCall] = []
                for _idx in sorted(accumulated_tool_calls):
                    entry = accumulated_tool_calls[_idx]
                    try:
                        args = json.loads(entry["arguments"] or "{}")
                    except (json.JSONDecodeError, TypeError):
                        args = {}
                    tool_calls.append(
                        ToolCall(id=entry["id"], name=entry["name"], input=args)
                    )

                yield {
                    "type": "final",
                    "response": LLMResponse(
                        text=accumulated_text,
                        tool_calls=tool_calls,
                        raw=None,
                    ),
                }
                return
            except Exception as exc:
                if attempt >= self.max_retries or not self._is_retryable_error(exc):
                    raise
                await asyncio.sleep(delay_s)
                delay_s = min(delay_s * 2, 8.0)

        raise RuntimeError("unreachable")  # pragma: no cover
