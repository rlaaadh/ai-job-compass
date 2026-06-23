from __future__ import annotations

from typing import Iterable, Optional

from src.db.models import Company, CompanyMonthlyStats
from src.scoring.health_score import calculate_health_score, _safe_int
from src.scoring.schemas import HealthScoreResult, RecommendationResult


def _verdict_for(diff: int) -> str:
    """건강도 점수 차이(target - current)로 이직 판정."""
    if diff >= 15:
        return "강력 추천"
    if diff >= 5:
        return "추천"
    if diff >= -5:
        return "중립"
    return "비추천"


def _recommendation_score(diff: int) -> int:
    """점수 차이를 0-100 추천 점수로 변환. 차이 0 → 50점 기준."""
    score = 50 + diff * 2  # +25점 차이면 만점 근처
    return int(round(max(0, min(100, score))))


def calculate_recommendation(
    current: HealthScoreResult,
    target: HealthScoreResult,
    current_company: Optional[Company] = None,
    target_company: Optional[Company] = None,
) -> RecommendationResult:
    """현재 회사와 관심 회사의 건강도를 비교해 이직 추천도를 계산한다.

    current/target: 각 회사의 HealthScoreResult.
    current_company/target_company: salary_change_signal 계산용 (참고값).
      당월고지금액 차이 — 실제 급여와 다른 참고 신호다.
    """
    diff = target.total - current.total
    score = _recommendation_score(diff)
    verdict = _verdict_for(diff)

    # 연봉 변화 추정 (참고값) — 국민연금 고지금액 차이, 실제 급여와 다름
    salary_change_signal = 0
    if current_company is not None and target_company is not None:
        salary_change_signal = _safe_int(target_company.monthly_charge_amt) - _safe_int(
            current_company.monthly_charge_amt
        )

    summary = {
        "total_diff": diff,
        "growth_diff": target.growth - current.growth,
        "stability_diff": target.stability - current.stability,
        "hiring_activity_diff": target.hiring_activity - current.hiring_activity,
        "size_fit_diff": target.size_fit - current.size_fit,
        "salary_signal_diff": target.salary_signal - current.salary_signal,
        "risk_penalty_diff": target.risk_penalty - current.risk_penalty,
        "current_grade": current.grade,
        "target_grade": target.grade,
        "salary_change_note": "국민연금 고지금액 기반 참고값 — 실제 급여 변화와 다름",
    }

    return RecommendationResult(
        score=score,
        current_company=current,
        target_company=target,
        salary_change_signal=salary_change_signal,
        summary=summary,
        verdict=verdict,
    )


def recommend_from_raw(
    current_company: Company,
    current_stats: Optional[Iterable[CompanyMonthlyStats]],
    target_company: Company,
    target_stats: Optional[Iterable[CompanyMonthlyStats]],
) -> RecommendationResult:
    """원천 데이터(Company + 월별 통계)로 건강도 계산부터 추천까지 한 번에 수행."""
    current = calculate_health_score(current_company, current_stats)
    target = calculate_health_score(target_company, target_stats)
    return calculate_recommendation(
        current, target, current_company, target_company
    )
