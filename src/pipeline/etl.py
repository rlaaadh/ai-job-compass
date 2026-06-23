from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from src.db.models import Company, CompanyMonthlyStats, WithdrawnCompany
from src.pipeline.nps_client import NPSClient


def upsert_company(session: Session, raw: dict) -> Company:
    seq = int(raw["seq"])
    company = session.get(Company, seq) or Company(seq=seq)
    company.name             = raw.get("wkplNm", "")
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
    company.synced_at        = datetime.utcnow()
    session.merge(company)
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
    results = client.search_establishment(name)
    if not results:
        return None

    raw_basic = results[0]
    seq = int(raw_basic["seq"])

    detail = client.get_establishment_detail(seq) or raw_basic
    merged = {**raw_basic, **detail}
    company = upsert_company(session, merged)

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


def _int(val) -> int | None:
    if val is None:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None
