#!/usr/bin/env python3
"""Small CLI for testing National Pension Service OpenAPI endpoints."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen


ENV_FILE = Path(".env")
API_KEY_ENV = "NPS_API_KEY"

ESTABLISHMENT_BASE_URL = "https://apis.data.go.kr/B552015/NpsBplcInfoInqireServiceV2"
WITHDRAWN_BASE_URL = "https://apis.data.go.kr/B552015/NpsScsnBplcInfoInqireServiceV2"


def load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("\"'")
    return values


def get_api_key() -> str:
    env_values = load_env_file(ENV_FILE)
    api_key = env_values.get(API_KEY_ENV, "")
    if api_key:
        return api_key

    print(
        f"{API_KEY_ENV} is missing. Fill it in {ENV_FILE} before running this script.",
        file=sys.stderr,
    )
    raise SystemExit(1)


def normalize_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    payload = unwrap_payload(payload)
    body = payload.get("body") or {}
    items = body.get("items") or {}
    item = items.get("item")

    if item is None:
        return []
    if isinstance(item, list):
        return item
    if isinstance(item, dict):
        return [item]
    return []


def request_json(base_url: str, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
    query = {
        "serviceKey": get_api_key(),
        "dataType": "json",
        **{key: value for key, value in params.items() if value not in (None, "")},
    }
    url = f"{base_url}{endpoint}?{urlencode(query)}"

    with urlopen(url) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        content = response.read().decode(charset)
    return json.loads(content)


def unwrap_payload(payload: dict[str, Any]) -> dict[str, Any]:
    response = payload.get("response")
    if isinstance(response, dict):
        return response
    return payload


def print_summary(payload: dict[str, Any]) -> None:
    payload = unwrap_payload(payload)
    header = payload.get("header") or {}
    body = payload.get("body") or {}
    items = normalize_items(payload)

    print(f"resultCode: {header.get('resultCode')}")
    print(f"resultMsg: {header.get('resultMsg')}")
    print(f"totalCount: {body.get('totalCount')}")
    print(f"pageNo: {body.get('pageNo')}")
    print(f"numOfRows: {body.get('numOfRows')}")
    print(f"items: {len(items)}")

    if items:
        first_item = items[0]
        preview_keys = [
            "wkplNm",
            "seq",
            "dataCrtYm",
            "jnngpCnt",
            "nwAcqzrCnt",
            "lssJnngpCnt",
            "crrmmNtcAmt",
            "scsnDt",
            "wkplRoadNmDtlAddr",
        ]
        preview = {key: first_item.get(key) for key in preview_keys if key in first_item}
        print("firstItemPreview:")
        print(json.dumps(preview, ensure_ascii=False, indent=2))


def maybe_save(payload: dict[str, Any], save_path: str | None) -> None:
    if not save_path:
        return

    path = Path(save_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"savedTo: {path}")


def run_command(args: argparse.Namespace) -> None:
    params = {
        "wkplNm": getattr(args, "name", None),
        "seq": getattr(args, "seq", None),
        "dataCrtYm": getattr(args, "year_month", None),
        "ldongAddrMgplDgCd": getattr(args, "sido_code", None),
        "ldongAddrMgplSgguCd": getattr(args, "sigungu_code", None),
        "ldongAddrMgplSgguEmdCd": getattr(args, "emd_code", None),
        "bzowrRgstNo": getattr(args, "business_number_prefix", None),
        "pageNo": args.page,
        "numOfRows": args.rows,
    }

    payload = request_json(args.base_url, args.endpoint, params)
    print_summary(payload)
    print()
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    maybe_save(payload, args.save)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Test National Pension Service OpenAPI endpoints."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_common_search_options(subparser: argparse.ArgumentParser) -> None:
        subparser.add_argument("--page", default="1", help="Page number")
        subparser.add_argument("--rows", default="10", help="Rows per page")
        subparser.add_argument("--save", help="Optional path to save raw JSON")

    def add_location_options(subparser: argparse.ArgumentParser) -> None:
        subparser.add_argument("--sido-code", help="법정동 시도 코드")
        subparser.add_argument("--sigungu-code", help="법정동 시군구 코드")
        subparser.add_argument("--emd-code", help="법정동 읍면동 코드")
        subparser.add_argument(
            "--business-number-prefix",
            help="사업자등록번호 앞 6자리",
        )

    est_basic = subparsers.add_parser(
        "establishment-basic",
        help="Search establishment basic info by company name",
    )
    est_basic.set_defaults(
        base_url=ESTABLISHMENT_BASE_URL,
        endpoint="/getBassInfoSearchV2",
    )
    est_basic.add_argument("--name", required=True, help="사업장명")
    add_location_options(est_basic)
    add_common_search_options(est_basic)

    est_detail = subparsers.add_parser(
        "establishment-detail",
        help="Get establishment detail info by seq",
    )
    est_detail.set_defaults(
        base_url=ESTABLISHMENT_BASE_URL,
        endpoint="/getDetailInfoSearchV2",
    )
    est_detail.add_argument("--seq", required=True, help="식별번호")
    add_common_search_options(est_detail)

    est_period = subparsers.add_parser(
        "establishment-period",
        help="Get establishment monthly status by seq",
    )
    est_period.set_defaults(
        base_url=ESTABLISHMENT_BASE_URL,
        endpoint="/getPdAcctoSttusInfoSearchV2",
    )
    est_period.add_argument("--seq", required=True, help="식별번호")
    est_period.add_argument("--year-month", help="조회 년월 (yyyymm)")
    add_common_search_options(est_period)

    withdrawn_basic = subparsers.add_parser(
        "withdrawn-basic",
        help="Search withdrawn establishment basic info by company name",
    )
    withdrawn_basic.set_defaults(
        base_url=WITHDRAWN_BASE_URL,
        endpoint="/getBassInfoSearchV2",
    )
    withdrawn_basic.add_argument("--name", required=True, help="사업장명")
    add_location_options(withdrawn_basic)
    add_common_search_options(withdrawn_basic)

    withdrawn_detail = subparsers.add_parser(
        "withdrawn-detail",
        help="Get withdrawn establishment detail info by seq",
    )
    withdrawn_detail.set_defaults(
        base_url=WITHDRAWN_BASE_URL,
        endpoint="/getDetailInfoSearchV2",
    )
    withdrawn_detail.add_argument("--seq", required=True, help="식별번호")
    add_common_search_options(withdrawn_detail)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    run_command(args)


if __name__ == "__main__":
    main()
