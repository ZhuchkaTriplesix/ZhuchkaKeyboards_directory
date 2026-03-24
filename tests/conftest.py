"""Ensure config.ini exists so imports from src.config succeed during test collection."""

from __future__ import annotations

import asyncio
import configparser
import shutil
from pathlib import Path

import pytest
from sqlalchemy import text

_ROOT = Path(__file__).resolve().parent.parent
_CFG = _ROOT / "config.ini"
_EXAMPLE = _ROOT / "config.ini.example"


def pytest_configure() -> None:
    if not _CFG.is_file() and _EXAMPLE.is_file():
        shutil.copy(_EXAMPLE, _CFG)
    elif _CFG.is_file() and _EXAMPLE.is_file():
        cfg = configparser.ConfigParser()
        cfg.read(_CFG)
        if not cfg.has_section("AUTH"):
            ex = configparser.ConfigParser()
            ex.read(_EXAMPLE)
            if ex.has_section("AUTH"):
                cfg["AUTH"] = dict(ex["AUTH"])
                with _CFG.open("w", encoding="utf-8") as f:
                    cfg.write(f)


@pytest.fixture(scope="session")
def postgres_reachable() -> None:
    """Skip integration tests if the app cannot open a DB connection."""
    from src.database.core import engine

    async def ping() -> None:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))

    try:
        asyncio.run(ping())
    except Exception as exc:
        pytest.skip(f"Postgres not reachable for integration tests: {exc}")
