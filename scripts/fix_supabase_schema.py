#!/usr/bin/env python3
"""Apply lightweight schema fixes for the remote Postgres database."""

from __future__ import annotations

from pathlib import Path
import sys

from sqlalchemy import text

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.db.models import get_engine  # noqa: E402


def main() -> int:
    engine = get_engine()
    statements = [
        """
        ALTER TABLE companies
        ALTER COLUMN monthly_charge_amt TYPE BIGINT
        """,
    ]

    with engine.begin() as conn:
        for statement in statements:
            conn.execute(text(statement))

    print("schema updated: companies.monthly_charge_amt -> BIGINT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
