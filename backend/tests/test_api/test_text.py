from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import app

from app.api.deps import require_admin

app.dependency_overrides[require_admin] = lambda: None

client = TestClient(app)


def test_generate_text_success(monkeypatch):
    """测试文本生成成功"""

    async def fake_generate(self, *, prompt, max_tokens, temperature, **kwargs):
        return "Generated text response"

    from app.services import text as text_module

    monkeypatch.setattr(text_module.TextService, "generate", fake_generate)

    response = client.post(
        "/api/v1/text/generate",
        json={"prompt": "Hello", "max_tokens": 100, "temperature": 0.7},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["text"] == "Generated text response"
    assert "model" in data


def test_generate_text_with_messages(monkeypatch):
    """测试多轮对话"""

    async def fake_generate(self, *, prompt, max_tokens, temperature, **kwargs):
        assert "messages" in kwargs
        assert kwargs["messages"] == [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hi"},
        ]
        return "Response with context"

    from app.services import text as text_module

    monkeypatch.setattr(text_module.TextService, "generate", fake_generate)

    response = client.post(
        "/api/v1/text/generate",
        json={
            "prompt": "ignored",
            "messages": [
                {"role": "system", "content": "You are helpful"},
                {"role": "user", "content": "Hi"},
            ],
        },
    )

    assert response.status_code == 200
    assert response.json()["text"] == "Response with context"


def test_generate_text_validation_error():
    """测试参数验证"""
    response = client.post(
        "/api/v1/text/generate",
        json={"max_tokens": 100},  # 缺少 prompt
    )

    assert response.status_code == 422


def test_generate_text_max_tokens_validation():
    """测试 max_tokens 范围验证"""
    response = client.post(
        "/api/v1/text/generate",
        json={"prompt": "test", "max_tokens": 10000},  # 超过 8192
    )

    assert response.status_code == 422


def test_generate_text_temperature_validation():
    """测试 temperature 范围验证"""
    response = client.post(
        "/api/v1/text/generate",
        json={"prompt": "test", "temperature": 3.0},  # 超过 2.0
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_stream_text_success(monkeypatch):
    """测试流式文本生成"""

    async def fake_stream(self, *, prompt, max_tokens, temperature, **kwargs):
        for chunk in ["Hello", " ", "world"]:
            yield chunk

    from app.services import text as text_module

    monkeypatch.setattr(text_module.TextService, "stream", fake_stream)

    response = client.post(
        "/api/v1/text/stream",
        json={"prompt": "Hello"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/plain; charset=utf-8"

    content = b"".join(response.iter_bytes())
    assert content == b"Hello world"


def test_stream_text_with_messages(monkeypatch):
    """测试流式多轮对话"""

    async def fake_stream(self, *, prompt, max_tokens, temperature, **kwargs):
        assert "messages" in kwargs
        yield "Streaming response"

    from app.services import text as text_module

    monkeypatch.setattr(text_module.TextService, "stream", fake_stream)

    response = client.post(
        "/api/v1/text/stream",
        json={
            "prompt": "ignored",
            "messages": [{"role": "user", "content": "Hi"}],
        },
    )

    assert response.status_code == 200
