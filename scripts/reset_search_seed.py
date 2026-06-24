#!/usr/bin/env python3
"""Clear search seed tables so they can be rebuilt cleanly."""

from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.db.models import (  # noqa: E402
    Company,
    CompanyMonthlyStats,
    CompanySearchAlias,
    WithdrawnCompany,
    get_session,
)


def main() -> int:
    session = get_session()
    try:
        deleted_aliases = session.query(CompanySearchAlias).delete(synchronize_session=False)
        deleted_stats = session.query(CompanyMonthlyStats).delete(synchronize_session=False)
        deleted_withdrawn = session.query(WithdrawnCompany).delete(synchronize_session=False)
        deleted_companies = session.query(Company).delete(synchronize_session=False)
        session.commit()
    finally:
        session.close()

    print(
        "deleted:",
        f"companies={deleted_companies}",
        f"aliases={deleted_aliases}",
        f"stats={deleted_stats}",
        f"withdrawn={deleted_withdrawn}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
