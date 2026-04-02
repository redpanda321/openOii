from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ProjectCreate(BaseModel):
    title: str = Field(min_length=1)
    story: str | None = None
    style: str | None = None
    status: str | None = None


class ProjectUpdate(BaseModel):
    title: str | None = None
    story: str | None = None
    style: str | None = None
    status: str | None = None


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    story: str | None
    style: str | None
    summary: str | None
    video_url: str | None
    status: str
    created_at: datetime
    updated_at: datetime
    hanggent_user_id: int | None = None


class ProjectListRead(BaseModel):
    items: list[ProjectRead]
    total: int


class CharacterRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    name: str
    description: str | None
    image_url: str | None


class ShotRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    order: int
    description: str
    prompt: str | None
    image_prompt: str | None
    image_url: str | None
    video_url: str | None
    duration: float | None


class ShotUpdate(BaseModel):
    order: int | None = Field(default=None, ge=1)
    description: str | None = None
    prompt: str | None = None
    image_prompt: str | None = None


class CharacterUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    description: str | None = None


class RegenerateRequest(BaseModel):
    type: Literal["image", "video"]


class GenerateRequest(BaseModel):
    notes: str | None = None


class FeedbackRequest(BaseModel):
    content: str


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    run_id: int | None = None
    agent: str
    role: str
    content: str
    progress: float | None = None
    is_loading: bool = False
    created_at: datetime


class AgentRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    status: str
    current_agent: str | None = None
    progress: float = 0.0
    error: str | None = None
    created_at: datetime
    updated_at: datetime
