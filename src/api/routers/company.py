from __future__ import annotations

import time

from fastapi import APIRouter, HTTPException
from sqlalchemy import func, or_

from src.api.deps import (
    build_health_response,
    company_to_basic,
    fetch_company_bundle,
    raw_to_company,
)
from src.ai.report_generator import ReportGenerator
from src.api.schemas import CompanyBasicResponse, HealthScoreResponse
from src.db.models import Company, CompanySearchAlias, get_session
from src.db.search_normalizer import normalize_company_name
from src.pipeline.nps_client import NPSClient
from src.scoring.health_score import calculate_health_score

router = APIRouter(prefix="/companies", tags=["companies"])

_SEARCH_CACHE_TTL_SECONDS = 60
_search_cache: dict[tuple[str, int], tuple[float, list[CompanyBasicResponse]]] = {}


def _search_companies_from_db(name: str, rows: int) -> list[CompanyBasicResponse]:
    normalized_query = normalize_company_name(name)
    if not normalized_query:
        return []

    session = get_session()
    try:
        alias_seq_query = (
            session.query(CompanySearchAlias.seq)
            .filter(CompanySearchAlias.normalized_alias_text.like(f"{normalized_query}%"))
        )

        base_query = (
            session.query(Company)
            .filter(
                or_(
                    Company.normalized_name.like(f"{normalized_query}%"),
                    Company.name_initials.like(f"{normalized_query}%"),
                    Company.seq.in_(alias_seq_query),
                )
            )
            .order_by(
                Company.search_rank.desc(),
                func.coalesce(Company.employee_count, 0).desc(),
                Company.name.asc(),
            )
            .limit(rows)
        )

        companies = [company_to_basic(company) for company in base_query.all()]
        if companies:
            return companies

        alias_contains_query = (
            session.query(CompanySearchAlias.seq)
            .filter(CompanySearchAlias.normalized_alias_text.like(f"%{normalized_query}%"))
        )

        fallback_query = (
            session.query(Company)
            .filter(
                or_(
                    Company.normalized_name.like(f"%{normalized_query}%"),
                    Company.seq.in_(alias_contains_query),
                )
            )
            .order_by(
                Company.search_rank.desc(),
                func.coalesce(Company.employee_count, 0).desc(),
                Company.name.asc(),
            )
            .limit(rows)
        )
        return [company_to_basic(company) for company in fallback_query.all()]
    finally:
        session.close()


def _search_companies_from_nps(name: str, rows: int) -> list[CompanyBasicResponse]:
    client = NPSClient()
    results = client.search_establishment(name, rows=rows)

    companies: list[CompanyBasicResponse] = []
    for raw in results:
        try:
            companies.append(company_to_basic(raw_to_company(raw)))
        except (TypeError, ValueError):
            # 외부 API 응답에 비정상 레코드가 섞여 있어도 검색 전체를 실패시키지 않는다.
            continue
    return companies


@router.get("/search", response_model=list[CompanyBasicResponse])
async def search_companies(
    name: str,
    rows: int = 10,
    fallback: bool = True,
) -> list[CompanyBasicResponse]:
    """회사명으로 사업장을 검색한다. 결과 없으면 빈 리스트."""
    normalized_name = name.strip()
    if len(normalized_name) < 2:
        return []

    cache_key = (normalized_name, rows)
    cached = _search_cache.get(cache_key)
    if cached and time.time() - cached[0] <= _SEARCH_CACHE_TTL_SECONDS:
        return cached[1]

    try:
        companies = _search_companies_from_db(normalized_name, rows)
    except Exception:
        companies = []

    if not companies and fallback:
        try:
            companies = _search_companies_from_nps(normalized_name, rows)
        except Exception as exc:  # NPS API 호출 실패
            if cached:
                return cached[1]
            raise HTTPException(status_code=503, detail=f"국민연금 API 호출 실패: {exc}")

    _search_cache[cache_key] = (time.time(), companies)
    return companies


@router.get("/{seq}/health", response_model=HealthScoreResponse)
async def get_company_health(seq: int) -> HealthScoreResponse:
    """단일 기업의 건강도 점수 + AI 리포트를 반환한다."""
    client = NPSClient()
    try:
        bundle = fetch_company_bundle(client, seq)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"국민연금 API 호출 실패: {exc}")

    if bundle is None:
        raise HTTPException(status_code=404, detail="해당 기업을 찾을 수 없습니다.")

    company, stats = bundle
    score = calculate_health_score(company, stats)

    generator = ReportGenerator()
    return build_health_response(company, stats, score, generator)
