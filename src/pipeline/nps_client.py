from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen
from urllib.error import URLError

_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
_ESTABLISHMENT_BASE = "https://apis.data.go.kr/B552015/NpsBplcInfoInqireServiceV2"
_WITHDRAWN_BASE = "https://apis.data.go.kr/B552015/NpsScsnBplcInfoInqireServiceV2"


def _load_api_key() -> str:
    env_value = os.environ.get("NPS_API_KEY")
    if env_value:
        return env_value.strip().strip("\"'")

    if _ENV_FILE.exists():
        for line in _ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("NPS_API_KEY="):
                return line.split("=", 1)[1].strip().strip("\"'")
    raise EnvironmentError("NPS_API_KEY not found in environment or .env")


def _request(base_url: str, endpoint: str, params: dict[str, Any], retries: int = 2) -> dict:
    api_key = _load_api_key()
    query = {"serviceKey": api_key, "dataType": "json",
             **{k: v for k, v in params.items() if v not in (None, "")}}
    url = f"{base_url}{endpoint}?{urlencode(query)}"
    for attempt in range(retries + 1):
        try:
            with urlopen(url, timeout=12) as resp:
                charset = resp.headers.get_content_charset() or "utf-8"
                return json.loads(resp.read().decode(charset))
        except (URLError, OSError, ValueError):
            if attempt == retries:
                raise
            time.sleep(1)
    return {}


def _items(payload: dict) -> list[dict]:
    resp = payload.get("response", payload)
    body = resp.get("body") or {}
    raw = (body.get("items") or {}).get("item")
    if raw is None:
        return []
    return raw if isinstance(raw, list) else [raw]


class NPSClient:
    def search_establishment(
        self, name: str, page: int = 1, rows: int = 10
    ) -> list[dict]:
        payload = _request(
            _ESTABLISHMENT_BASE, "/getBassInfoSearchV2",
            {"wkplNm": name, "pageNo": page, "numOfRows": rows},
        )
        return _items(payload)

    def get_establishment_detail(self, seq: int | str) -> dict | None:
        payload = _request(
            _ESTABLISHMENT_BASE, "/getDetailInfoSearchV2",
            {"seq": seq, "numOfRows": 1},
        )
        items = _items(payload)
        return items[0] if items else None

    def get_monthly_stats(
        self, seq: int | str, year_month: str | None = None
    ) -> list[dict]:
        payload = _request(
            _ESTABLISHMENT_BASE, "/getPdAcctoSttusInfoSearchV2",
            {"seq": seq, "dataCrtYm": year_month, "numOfRows": 24},
        )
        return _items(payload)

    def search_withdrawn(
        self, name: str, page: int = 1, rows: int = 10
    ) -> list[dict]:
        payload = _request(
            _WITHDRAWN_BASE, "/getBassInfoSearchV2",
            {"wkplNm": name, "pageNo": page, "numOfRows": rows},
        )
        return _items(payload)

    def get_withdrawn_detail(self, seq: int | str) -> dict | None:
        payload = _request(
            _WITHDRAWN_BASE, "/getDetailInfoSearchV2",
            {"seq": seq, "numOfRows": 1},
        )
        items = _items(payload)
        return items[0] if items else None
