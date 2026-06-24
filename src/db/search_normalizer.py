from __future__ import annotations

import re
from typing import Iterable

_LEGAL_PATTERNS = (
    "(주)",
    "（주）",
    "㈜",
    "주식회사",
    "（유）",
    "(유)",
    "유한회사",
    "합자회사",
    "합명회사",
)

_NON_WORD_RE = re.compile(r"[^0-9A-Za-z가-힣]+")

_INITIALS = [
    "ㄱ", "ㄲ", "ㄴ", "ㄷ", "ㄸ", "ㄹ", "ㅁ", "ㅂ", "ㅃ",
    "ㅅ", "ㅆ", "ㅇ", "ㅈ", "ㅉ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ",
]


def normalize_company_name(name: str | None) -> str:
    """회사명을 검색 친화적인 형태로 정규화한다."""
    if not name:
        return ""

    normalized = name.strip()
    for pattern in _LEGAL_PATTERNS:
        normalized = normalized.replace(pattern, " ")
    normalized = _NON_WORD_RE.sub("", normalized)
    return normalized.lower()


def extract_name_initials(name: str | None) -> str:
    """한글 초성/영문 이니셜 기반 검색 보조 문자열을 만든다."""
    if not name:
        return ""

    normalized = normalize_company_name(name)
    initials: list[str] = []
    for char in normalized:
        code = ord(char)
        if 0xAC00 <= code <= 0xD7A3:
            initial_index = (code - 0xAC00) // 588
            initials.append(_INITIALS[initial_index])
        elif char.isalnum():
            initials.append(char[0])
    return "".join(initials)


def build_company_aliases(name: str | None) -> list[str]:
    """회사명 검색에 도움 되는 alias 후보를 만든다."""
    if not name:
        return []

    raw = name.strip()
    variants = {
        raw,
        normalize_company_name(raw),
    }

    compact = _NON_WORD_RE.sub("", raw)
    if compact:
        variants.add(compact)

    legal_stripped = raw
    for pattern in _LEGAL_PATTERNS:
        legal_stripped = legal_stripped.replace(pattern, " ")
    legal_stripped = " ".join(legal_stripped.split())
    if legal_stripped:
        variants.add(legal_stripped)
        variants.add(normalize_company_name(legal_stripped))

    return [alias for alias in variants if alias]


def unique_preserving_order(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered
