from __future__ import annotations

from fastapi import APIRouter, HTTPException

from src.api.deps import (
    build_health_response,
    company_to_basic,
    fetch_company_bundle,
    raw_to_company,
)
from src.ai.report_generator import ReportGenerator
from src.api.schemas import CompanyBasicResponse, HealthScoreResponse
from src.pipeline.nps_client import NPSClient
from src.scoring.health_score import calculate_health_score

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("/search", response_model=list[CompanyBasicResponse])
async def search_companies(name: str, rows: int = 10) -> list[CompanyBasicResponse]:
    """회사명으로 사업장을 검색한다. 결과 없으면 빈 리스트."""
    client = NPSClient()
    try:
        results = client.search_establishment(name, rows=rows)
    except Exception as exc:  # NPS API 호출 실패
        raise HTTPException(status_code=503, detail=f"국민연금 API 호출 실패: {exc}")

    return [company_to_basic(raw_to_company(raw)) for raw in results]


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
    return build_health_response(company, score, generator)
