#!/usr/bin/env python3
"""Seed or refresh search-oriented company data into the configured DB."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.db.models import get_session, init_db, resolve_database_url
from src.pipeline.etl import sync_company_search_seed
from src.pipeline.nps_client import NPSClient


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sync company search data from NPS API into SQLite/Supabase DB."
    )
    parser.add_argument(
        "--name",
        action="append",
        default=[],
        help="회사명 하나를 동기화합니다. 여러 번 전달할 수 있습니다.",
    )
    parser.add_argument(
        "--file",
        help="회사명을 한 줄씩 적은 텍스트 파일 경로",
    )
    parser.add_argument(
        "--db-path",
        default="data/job_compass.db",
        help="SQLite fallback 경로입니다. SUPABASE_DB_URL이 있으면 무시됩니다.",
    )
    parser.add_argument(
        "--include-stats",
        action="store_true",
        help="월별 통계까지 함께 적재합니다. 검색 시드 용도라면 보통 끄는 것이 더 빠르고 안정적입니다.",
    )
    parser.add_argument(
        "--offset",
        type=int,
        default=0,
        help="파일 기반 입력일 때 앞에서부터 건너뛸 개수",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="파일 기반 입력일 때 이번 실행에서 처리할 최대 개수",
    )
    return parser.parse_args()


def load_names(args: argparse.Namespace) -> list[str]:
    names = [name.strip() for name in args.name if name.strip()]
    if args.file:
        file_path = Path(args.file)
        for line in file_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                names.append(line)
    unique_names = list(dict.fromkeys(names))

    if args.file:
        if args.offset > 0:
            unique_names = unique_names[args.offset:]
        if args.limit is not None:
            unique_names = unique_names[: args.limit]

    return unique_names


def main() -> int:
    args = parse_args()
    names = load_names(args)
    if not names:
        print("동기화할 회사명을 --name 또는 --file 로 전달해주세요.")
        return 1

    database_url = resolve_database_url(args.db_path)
    if database_url.startswith("sqlite:///"):
        print(f"[DB] using local SQLite: {args.db_path}")
    else:
        print("[DB] using configured PostgreSQL from environment")

    init_db(args.db_path)
    session = get_session(args.db_path)
    client = NPSClient()

    success = 0
    failed = 0

    try:
        for name in names:
            try:
                company = sync_company_search_seed(
                    client,
                    session,
                    name,
                    include_stats=args.include_stats,
                )
                if company is None:
                    failed += 1
                    print(f"[MISS] {name}: 검색 결과 없음")
                    continue

                success += 1
                print(
                    f"[OK] {name} -> seq={company.seq}, stored_name={company.name}, "
                    f"normalized={company.normalized_name}"
                )
            except Exception as exc:
                session.rollback()
                failed += 1
                print(f"[ERR] {name}: {exc}")
    finally:
        session.close()

    print(f"done: success={success}, failed={failed}")
    return 0 if success > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
