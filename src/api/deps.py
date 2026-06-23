"""API 라우터 공용 헬퍼.

NPS API 원천 데이터(raw dict)를 도메인 모델(Company / CompanyMonthlyStats)로
변환하고, 건강도 계산 + AI 리포트를 묶어 HealthScoreResponse로 만든다.

MVP 단순화: DB를 거치지 않고 NPS API를 직접 호출한다.
NPSClient / ReportGenerator는 요청마다 새로 생성한다 (상태 없음).
"""
from __future__ import annotations

from typing import Optional

from src.ai.report_generator import ReportGenerator
from src.api.schemas import (
    CompanyBasicResponse,
    CompanyReportResponse,
    HealthScoreResponse,
)
from src.db.models import Company, CompanyMonthlyStats
from src.pipeline.nps_client import NPSClient
from src.scoring.schemas import HealthScoreResult


def _int(val) -> int | None:
    if val is None:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


def raw_to_company(raw: dict) -> Company:
    """NPS 원천 dict를 Company ORM 객체(미저장)로 변환한다."""
    company = Company(seq=int(raw["seq"]))
    company.name = raw.get("wkplNm", "")
    company.business_reg_no = raw.get("bzowrRgstNo")
    company.address = raw.get("wkplRoadNmDtlAddr")
    company.industry_code = raw.get("wkplIntpCd")
    company.industry_name = raw.get("vldtVlKrnNm")
    company.workplace_type = raw.get("wkplStylDvcd")
    company.join_status = raw.get("wkplJnngStcd")
    company.join_date = raw.get("adptDt")
    company.employee_count = _int(raw.get("jnngpCnt"))
    company.monthly_charge_amt = _int(raw.get("crrmmNtcAmt"))
    company.sido_code = raw.get("ldongAddrMgplDgCd")
    company.sigungu_code = raw.get("ldongAddrMgplSgguCd")
    company.data_created_ym = raw.get("dataCrtYm")
    return company


def raw_to_monthly_stats(seq: int, raw_list: list[dict], base_ym: str | None) -> list[CompanyMonthlyStats]:
    """NPS 월별 통계 원천 리스트를 CompanyMonthlyStats 객체 리스트로 변환한다."""
    stats: list[CompanyMonthlyStats] = []
    for raw in raw_list:
        ym = raw.get("dataCrtYm") or base_ym
        if not ym:
            continue
        stat = CompanyMonthlyStats(seq=seq, year_month=ym)
        stat.new_joiners = _int(raw.get("nwAcqzrCnt"))
        stat.leavers = _int(raw.get("lssJnngpCnt"))
        stat.employee_count = _int(raw.get("jnngpCnt"))
        stats.append(stat)
    return stats


def fetch_company_bundle(
    client: NPSClient, seq: int
) -> Optional[tuple[Company, list[CompanyMonthlyStats]]]:
    """seq로 상세 + 월별 통계를 조회해 (Company, [월별통계])를 반환한다.

    기업을 찾지 못하면 None을 반환한다.
    """
    detail = client.get_establishment_detail(seq)
    if not detail:
        return None

    detail = {**detail, "seq": seq}
    company = raw_to_company(detail)

    base_ym = detail.get("dataCrtYm")
    raw_stats = client.get_monthly_stats(seq, year_month=base_ym)
    stats = raw_to_monthly_stats(seq, raw_stats, base_ym)
    return company, stats


def company_to_basic(company: Company) -> CompanyBasicResponse:
    return CompanyBasicResponse(
        seq=company.seq,
        name=company.name,
        address=company.address,
        industry_name=company.industry_name,
        employee_count=company.employee_count,
        join_status=company.join_status,
    )


def build_health_response(
    company: Company,
    score: HealthScoreResult,
    generator: ReportGenerator,
) -> HealthScoreResponse:
    """건강도 점수 + AI 리포트를 묶어 HealthScoreResponse를 만든다.

    AI 리포트 생성에 실패해도 ai_report=None으로 두고 점수는 항상 반환한다.
    """
    ai_report: CompanyReportResponse | None = None
    try:
        report = generator.generate_company_report(score, company.name)
        ai_report = CompanyReportResponse(
            summary=report.summary,
            growth_comment=report.growth_comment,
            stability_comment=report.stability_comment,
            hiring_comment=report.hiring_comment,
        )
    except Exception:
        ai_report = None

    return HealthScoreResponse(
        seq=company.seq,
        name=company.name,
        health_score=score.total,
        grade=score.grade,
        growth=score.growth,
        stability=score.stability,
        hiring_activity=score.hiring_activity,
        breakdown=score.breakdown,
        ai_report=ai_report,
    )
