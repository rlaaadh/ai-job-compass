from __future__ import annotations

from fastapi import APIRouter, HTTPException

from src.ai.report_generator import ReportGenerator
from src.api.deps import build_health_response, fetch_company_bundle
from src.api.schemas import (
    CompareRequest,
    CompareResponse,
    RecommendationReportResponse,
)
from src.pipeline.nps_client import NPSClient
from src.scoring.health_score import calculate_health_score
from src.scoring.recommendation import calculate_recommendation

router = APIRouter(prefix="/compare", tags=["comparison"])


@router.post("", response_model=CompareResponse)
async def compare_companies(request: CompareRequest) -> CompareResponse:
    """현재 회사와 관심 회사를 비교해 이직 추천도 + AI 리포트를 반환한다."""
    client = NPSClient()
    try:
        current_bundle = fetch_company_bundle(client, request.current_seq)
        target_bundle = fetch_company_bundle(client, request.target_seq)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"국민연금 API 호출 실패: {exc}")

    if current_bundle is None or target_bundle is None:
        raise HTTPException(status_code=404, detail="비교 대상 기업을 찾을 수 없습니다.")

    current_company, current_stats = current_bundle
    target_company, target_stats = target_bundle

    current_score = calculate_health_score(current_company, current_stats)
    target_score = calculate_health_score(target_company, target_stats)

    rec = calculate_recommendation(
        current_score, target_score, current_company, target_company, request.role
    )

    generator = ReportGenerator()

    current_resp = build_health_response(current_company, current_score, generator)
    target_resp = build_health_response(target_company, target_score, generator)

    ai_report: RecommendationReportResponse | None = None
    try:
        report = generator.generate_recommendation_report(
            rec, current_company.name, target_company.name
        )
        ai_report = RecommendationReportResponse(
            summary=report.summary,
            risk_comment=report.risk_comment,
            salary_comment=report.salary_comment,
        )
    except Exception:
        ai_report = None

    return CompareResponse(
        recommendation_score=rec.score,
        verdict=rec.verdict,
        current=current_resp,
        target=target_resp,
        salary_change_signal=rec.salary_change_signal,
        ai_report=ai_report,
    )
