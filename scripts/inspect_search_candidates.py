#!/usr/bin/env python3
"""Inspect raw NPS search candidates for a company name."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.db.search_normalizer import normalize_company_name  # noqa: E402
from src.pipeline.nps_client import NPSClient  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True, help="조회할 회사명")
    parser.add_argument("--rows", type=int, default=20, help="가져올 후보 수")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    client = NPSClient()
    results = client.search_establishment(args.name, rows=args.rows)

    if not results:
        print("검색 결과가 없습니다.")
        return 1

    for index, raw in enumerate(results, start=1):
        print(
            f"{index:02d}. seq={raw.get('seq')} "
            f"name={raw.get('wkplNm')} "
            f"normalized={normalize_company_name(raw.get('wkplNm'))} "
            f"employees={raw.get('jnngpCnt')}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
