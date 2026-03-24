#!/usr/bin/env python3
"""Write config.ini for GitHub Actions (Postgres service container)."""

from __future__ import annotations

import configparser
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_EXAMPLE = _ROOT / "config.ini.example"
_OUT = _ROOT / "config.ini"


def main() -> None:
    cfg = configparser.ConfigParser()
    cfg.read(_EXAMPLE)
    cfg["POSTGRES"]["DATABASE_NAME"] = "zhuchka_directory_test"
    cfg["POSTGRES"]["USERNAME"] = "zhuchka"
    cfg["POSTGRES"]["PASSWORD"] = "zhuchka"
    cfg["POSTGRES"]["IP"] = "127.0.0.1"
    cfg["POSTGRES"]["PORT"] = "5432"
    with _OUT.open("w", encoding="utf-8") as f:
        cfg.write(f)


if __name__ == "__main__":
    main()
