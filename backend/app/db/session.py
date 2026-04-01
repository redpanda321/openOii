from __future__ import annotations

from collections.abc import AsyncGenerator

import asyncio
from sqlalchemy import func, inspect as sa_inspect, text, update
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.config import get_settings
from app.models import agent_run, config_item, message, project  # noqa: F401


def _patch_aiosqlite_event_loop() -> None:
    # Python 3.14 tightened asyncio.get_event_loop() semantics; older aiosqlite versions
    # may hang because they create futures on a non-running loop. Force it to use the
    # running loop when available.
    try:
        import aiosqlite.core as _core  # type: ignore
    except Exception:
        return

    try:
        _core.asyncio.get_event_loop = asyncio.get_running_loop  # type: ignore[attr-defined]
    except Exception:
        return


_patch_aiosqlite_event_loop()


def _build_engine() -> AsyncEngine:
    settings = get_settings()
    return create_async_engine(settings.database_url, echo=settings.db_echo, pool_pre_ping=True)


engine: AsyncEngine = _build_engine()
async_session_maker: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def _migrate_hanggent_user_id(conn) -> None:
    """Add hanggent_user_id column to project table if missing (for existing installs)."""
    def _check_column(sync_conn):
        inspector = sa_inspect(sync_conn)
        columns = [c["name"] for c in inspector.get_columns("project")]
        return "hanggent_user_id" in columns

    has_column = await conn.run_sync(_check_column)
    if not has_column:
        await conn.execute(text(
            "ALTER TABLE project ADD COLUMN hanggent_user_id INTEGER"
        ))
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_project_hanggent_user_id "
            "ON project (hanggent_user_id)"
        ))
        await conn.commit()


async def init_db() -> None:
    """Initialize database tables and cleanup stale runs."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    # Migrate existing tables
    async with engine.connect() as conn:
        await _migrate_hanggent_user_id(conn)

    async with async_session_maker() as session:
        from app.services.config_service import ConfigService
        from app.models.agent_run import AgentRun
        from app.models.project import Project

        config_service = ConfigService(session)
        await config_service.ensure_initialized()
        await config_service.apply_settings_overrides()

        # 清理服务重启前遗留的 running/queued 状态的 run（它们已经不会继续执行了）
        await session.execute(
            update(AgentRun)
            .where(AgentRun.status.in_(["queued", "running"]))
            .values(status="cancelled", error="Service restarted")
        )

        # 兼容旧数据：style 可能为 NULL/空字符串，统一回填为默认风格
        await session.execute(
            update(Project)
            .where((Project.style.is_(None)) | (func.trim(Project.style) == ""))
            .values(style="anime")
        )
        await session.commit()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
