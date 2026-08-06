from pathlib import Path

import pytest
from app.core import settings


def test_resolve_relative_variants_equal() -> None:
    backend_dir = settings.BACKEND_DIRECTORY
    chat_db_path = (backend_dir / "data" / "chat.db").resolve().as_posix()
    expected = f"sqlite+aiosqlite:///{chat_db_path}"

    inputs = [
        "sqlite+aiosqlite:///./backend/data/chat.db",
        "sqlite+aiosqlite:///data/chat.db",
        "sqlite+aiosqlite:///backend/data/chat.db",
    ]

    for inp in inputs:
        out = settings.resolve_database_url(inp, backend_directory=backend_dir)
        assert out == expected


def test_resolve_absolute_and_memory_and_postgres_unchanged() -> None:
    backend_dir = settings.BACKEND_DIRECTORY
    abs_path = "sqlite+aiosqlite:///F:/Kernschmied/backend/data/chat.db"
    assert (
        settings.resolve_database_url(abs_path, backend_directory=backend_dir)
        == abs_path
    )

    memory = "sqlite+aiosqlite:///:memory:"
    assert (
        settings.resolve_database_url(memory, backend_directory=backend_dir) == memory
    )

    pg = "postgresql+asyncpg://user:pass@localhost/db"
    assert settings.resolve_database_url(pg, backend_directory=backend_dir) == pg


def test_resolve_is_cwd_independent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    backend_dir = settings.BACKEND_DIRECTORY
    inp = "sqlite+aiosqlite:///data/chat.db"

    monkeypatch.chdir(tmp_path)
    out = settings.resolve_database_url(inp, backend_directory=backend_dir)
    chat_db_path = (backend_dir / "data" / "chat.db").resolve().as_posix()
    expected = f"sqlite+aiosqlite:///{chat_db_path}"
    assert out == expected
