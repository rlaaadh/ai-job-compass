from __future__ import annotations

from datetime import datetime
from difflib import SequenceMatcher
import re

from sqlalchemy.orm import Session

from src.db.models import (
    Company,
    CompanyMonthlyStats,
    CompanySearchAlias,
    WithdrawnCompany,
)
from src.db.search_normalizer import (
    build_company_aliases,
    extract_name_initials,
    normalize_company_name,
    unique_preserving_order,
)
from src.pipeline.nps_client import NPSClient

_NOISY_NAME_PATTERNS = (
    "일용",
    "공사",
    "현장",
    "프로젝트",
    "hookup",
    "유지보수",
    "개발사업",
    "블럭",
    "본사부지",
    "어린이집",
    "유치원",
    "소방",
    "주유소",
)
_TOKEN_SPLIT_RE = re.compile(r"[\s/·,()（）\-]+")
_STRICT_SUFFIX_MAX_LEN = 0


def upsert_company(session: Session, raw: dict) -> Company:
    seq = int(raw["seq"])
    company = session.get(Company, seq) or Company(seq=seq)
    company.name             = raw.get("wkplNm", "")
    company.normalized_name  = normalize_company_name(company.name)
    company.name_initials    = extract_name_initials(company.name)
    company.business_reg_no  = raw.get("bzowrRgstNo")
    company.address          = raw.get("wkplRoadNmDtlAddr")
    company.industry_code    = raw.get("wkplIntpCd")
    company.industry_name    = raw.get("vldtVlKrnNm")
    company.workplace_type   = raw.get("wkplStylDvcd")
    company.join_status      = raw.get("wkplJnngStcd")
    company.join_date        = raw.get("adptDt")
    company.employee_count   = _int(raw.get("jnngpCnt"))
    company.monthly_charge_amt = _int(raw.get("crrmmNtcAmt"))
    company.sido_code        = raw.get("ldongAddrMgplDgCd")
    company.sigungu_code     = raw.get("ldongAddrMgplSgguCd")
    company.data_created_ym  = raw.get("dataCrtYm")
    company.search_rank      = _calculate_search_rank(company)
    company.synced_at        = datetime.utcnow()
    session.merge(company)
    replace_company_aliases(session, seq, build_company_aliases(company.name))
    return company


def upsert_monthly_stats(
    session: Session, seq: int, year_month: str, raw: dict
) -> CompanyMonthlyStats:
    existing = (
        session.query(CompanyMonthlyStats)
        .filter_by(seq=seq, year_month=year_month)
        .first()
    )
    stat = existing or CompanyMonthlyStats(seq=seq, year_month=year_month)
    stat.new_joiners    = _int(raw.get("nwAcqzrCnt"))
    stat.leavers        = _int(raw.get("lssJnngpCnt"))
    stat.employee_count = _int(raw.get("jnngpCnt"))
    session.merge(stat)
    return stat


def upsert_withdrawn(session: Session, raw: dict) -> WithdrawnCompany:
    seq = int(raw["seq"])
    w = session.get(WithdrawnCompany, seq) or WithdrawnCompany(seq=seq)
    w.name             = raw.get("wkplNm", "")
    w.business_reg_no  = raw.get("bzowrRgstNo")
    w.address          = raw.get("wkplRoadNmDtlAddr")
    w.withdrawal_date  = raw.get("scsnDt")
    session.merge(w)
    return w


def sync_company(client: NPSClient, session: Session, name: str) -> Company | None:
    """기업명으로 검색 → 상세 + 최근 24개월 월별 통계 동기화."""
    return sync_company_search_seed(client, session, name, include_stats=True)


def sync_company_search_seed(
    client: NPSClient,
    session: Session,
    name: str,
    include_stats: bool = False,
) -> Company | None:
    """검색용 회사 데이터를 동기화한다.

    include_stats=False면 검색 결과와 상세 정보 위주로만 저장해
    시드 적재 속도와 성공률을 높인다.
    """
    # 검색 시드 적재는 후보를 넓게 가져와야 대표 회사를 고를 확률이 높다.
    results = client.search_establishment(name, rows=50)
    if not results:
        return None

    raw_basic = _select_best_search_result(name, results)
    if raw_basic is None:
        return None
    seq = int(raw_basic["seq"])

    detail = client.get_establishment_detail(seq) or raw_basic
    merged = {**raw_basic, **detail}
    company = upsert_company(session, merged)

    if include_stats:
        # 월별 통계 적재.
        # 주의: period 응답에는 dataCrtYm 필드가 없으므로, 기준 년월을 호출 측에서 명시한다.
        # 기준 년월은 detail/basic 의 dataCrtYm(사업장 데이터 생성 년월)을 사용한다.
        base_ym = merged.get("dataCrtYm")
        for stat_raw in client.get_monthly_stats(seq, year_month=base_ym):
            ym = stat_raw.get("dataCrtYm") or base_ym
            if ym:
                upsert_monthly_stats(session, seq, ym, stat_raw)

    session.commit()
    return company


def replace_company_aliases(session: Session, seq: int, aliases: list[str]) -> None:
    session.query(CompanySearchAlias).filter_by(seq=seq).delete(synchronize_session=False)

    for alias in unique_preserving_order(aliases):
        normalized_alias = normalize_company_name(alias)
        if not normalized_alias:
            continue

        session.add(
            CompanySearchAlias(
                seq=seq,
                alias_text=alias,
                normalized_alias_text=normalized_alias,
                alias_type="normalized" if alias != normalized_alias else "official",
            )
        )


def _calculate_search_rank(company: Company) -> int:
    score = 0
    if company.join_status == "1":
        score += 20
    if company.employee_count:
        score += min(int(company.employee_count), 5000) // 50
    if company.data_created_ym:
        score += 10
    return score


def _select_best_search_result(name: str, results: list[dict]) -> dict | None:
    target = normalize_company_name(name)
    target_tokens = {token for token in _tokenize_name(name) if token}
    non_noisy_results = [raw for raw in results if not _is_noisy_candidate(raw)]
    candidates = non_noisy_results or results

    strict_candidates = [
        raw
        for raw in candidates
        if _is_strict_company_match(target, raw)
    ]
    if not strict_candidates:
        return None
    candidates = strict_candidates

    def candidate_score(raw: dict) -> tuple[float, int, int, int]:
        candidate_name = raw.get("wkplNm", "")
        normalized_candidate = normalize_company_name(candidate_name)
        candidate_tokens = {token for token in _tokenize_name(candidate_name) if token}

        exact = 1 if normalized_candidate == target else 0
        starts = 1 if normalized_candidate.startswith(target) else 0
        contains = 1 if target and target in normalized_candidate else 0
        similarity = SequenceMatcher(None, target, normalized_candidate).ratio()
        token_overlap = len(target_tokens & candidate_tokens)

        employee_count = _int(raw.get("jnngpCnt")) or 0
        extra_suffix_len = max(0, len(normalized_candidate) - len(target))
        length_penalty = -max(0, extra_suffix_len - 2)
        noisy_penalty = -sum(
            4 for pattern in _NOISY_NAME_PATTERNS if pattern in candidate_name.lower()
        )
        punctuation_penalty = -2 if "/" in candidate_name else 0
        suffix_penalty = -3 if normalized_candidate.endswith(("토", "후드")) else 0
        exact_token_bonus = 1 if target in candidate_tokens else 0

        return (
            exact * 100
            + exact_token_bonus * 40
            + starts * 25
            + contains * 10
            + token_overlap * 6
            + similarity
            + noisy_penalty
            + punctuation_penalty
            + suffix_penalty,
            employee_count,
            length_penalty,
            -len(candidate_name),
        )

    return max(candidates, key=candidate_score)


def _tokenize_name(name: str | None) -> list[str]:
    if not name:
        return []
    return [
        normalize_company_name(token)
        for token in _TOKEN_SPLIT_RE.split(name)
        if normalize_company_name(token)
    ]


def _is_noisy_candidate(raw: dict) -> bool:
    name = (raw.get("wkplNm") or "").lower()
    if "/" in name:
        return True
    return any(pattern in name for pattern in _NOISY_NAME_PATTERNS)


def _is_strict_company_match(
    target: str,
    raw: dict,
) -> bool:
    candidate_name = raw.get("wkplNm", "")
    normalized_candidate = normalize_company_name(candidate_name)

    if not target or not normalized_candidate:
        return False

    if normalized_candidate == target:
        return True

    if normalized_candidate.startswith(target):
        extra_suffix_len = len(normalized_candidate) - len(target)
        if extra_suffix_len <= _STRICT_SUFFIX_MAX_LEN:
            return True

    return False


def _int(val) -> int | None:
    if val is None:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None
