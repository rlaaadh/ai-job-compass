from __future__ import annotations

import re
from typing import Iterable, Optional

from src.db.models import Company, CompanyMonthlyStats
from src.scoring.health_score import calculate_health_score, _safe_int
from src.scoring.schemas import HealthScoreResult, RecommendationResult

_NON_WORD_RE = re.compile(r"[^0-9a-z가-힣]+")
_TECH_ROLE_KEYWORDS = (
    "프론트",
    "프론트엔드",
    "frontend",
    "react",
    "vue",
    "web",
    "웹",
    "ios",
    "android",
    "app",
    "앱",
    "개발",
    "developer",
    "engineer",
    "엔지니어",
)
_TECH_COMPANY_KEYWORDS = (
    "소프트웨어",
    "응용 소프트웨어",
    "시스템 소프트웨어",
    "컴퓨터시스템 통합",
    "포털",
    "데이터베이스",
    "정보서비스",
    "온라인",
    "플랫폼",
    "전자상거래",
    "통신",
    "클라우드",
    "it",
    "ict",
    "인터넷",
    "모빌리티",
    "게임",
    "엔터테인먼트",
    "디지털",
)
_LOW_TECH_COMPANY_KEYWORDS = (
    "식품",
    "음료",
    "제조업",
    "도매업",
    "백화점",
    "마트",
    "유통",
    "제약",
    "화학",
)


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


def _estimate_annual_salary_signal(company: Optional[Company]) -> int:
    """국민연금 고지금액으로 1인당 연봉 참고값을 거칠게 추정한다.

    월 고지금액 / 직원 수 -> 1인당 월 고지금액
    이를 국민연금 총요율 9%의 참고값으로 보고 월 기준소득을 역산한 뒤 연간 환산한다.
    실제 연봉과 다를 수 있으므로 비교용 신호로만 사용한다.
    """
    if company is None:
        return 0

    charge = _safe_int(company.monthly_charge_amt)
    emp = _safe_int(company.employee_count)
    if charge <= 0 or emp <= 0:
        return 0

    per_capita_charge = charge / emp
    estimated_monthly_income = per_capita_charge / 0.09
    return int(round(estimated_monthly_income * 12))


def _salary_diff_score_adjustment(salary_change_signal: int) -> int:
    """연봉 변화 추정 신호를 추천도 보정 점수로 변환한다.

    직장인은 연봉 감소에 민감하므로 감소폭에는 더 큰 페널티를 준다.
    증가 신호는 더 적극적으로 가점하되, 건강도 점수를 완전히 덮지 않도록 상한을 둔다.
    """
    if salary_change_signal <= -20_000_000:
        return -15
    if salary_change_signal <= -15_000_000:
        return -12
    if salary_change_signal <= -10_000_000:
        return -9
    if salary_change_signal <= -5_000_000:
        return -6
    if salary_change_signal < 0:
        return -2

    if salary_change_signal >= 30_000_000:
        return 14
    if salary_change_signal >= 20_000_000:
        return 12
    if salary_change_signal >= 15_000_000:
        return 10
    if salary_change_signal >= 10_000_000:
        return 7
    if salary_change_signal >= 5_000_000:
        return 4
    return 0


def _normalize_text(value: str | None) -> str:
    if not value:
        return ""
    return _NON_WORD_RE.sub("", value.lower())


def _company_role_fit(company: Optional[Company], role: str | None) -> int:
    """직무와 회사 속성의 대략적인 적합도를 0~4로 계산한다."""
    normalized_role = _normalize_text(role)
    if not normalized_role or company is None:
        return 0

    role_text = f"{company.name or ''} {company.industry_name or ''}".lower()
    normalized_company_text = _normalize_text(role_text)

    if any(keyword in normalized_role for keyword in _TECH_ROLE_KEYWORDS):
        high_match = sum(1 for keyword in _TECH_COMPANY_KEYWORDS if keyword in role_text)
        low_match = sum(1 for keyword in _LOW_TECH_COMPANY_KEYWORDS if keyword in role_text)

        if high_match >= 2:
            return 4
        if high_match >= 1:
            return 3
        if any(keyword in normalized_company_text for keyword in ("네이버", "카카오", "라인", "토스", "쿠팡", "당근", "리디", "야놀자", "스마일게이트", "넥슨", "넷마블", "크래프톤", "펄어비스", "엔씨", "삼성에스디에스", "엘지씨엔에스", "포스코디엑스")):
            return 3
        if low_match >= 1:
            return 1
        return 2

    return 0


def calculate_recommendation(
    current: HealthScoreResult,
    target: HealthScoreResult,
    current_company: Optional[Company] = None,
    target_company: Optional[Company] = None,
    role: str | None = None,
) -> RecommendationResult:
    """현재 회사와 관심 회사의 건강도를 비교해 이직 추천도를 계산한다.

    current/target: 각 회사의 HealthScoreResult.
    current_company/target_company: salary_change_signal 계산용 (참고값).
      당월고지금액 차이 — 실제 급여와 다른 참고 신호다.
    """
    diff = target.total - current.total
    current_role_fit = _company_role_fit(current_company, role)
    target_role_fit = _company_role_fit(target_company, role)
    role_fit_delta = target_role_fit - current_role_fit

    # 연봉 변화 추정 (참고값) — 1인당 추정 연봉 신호 차이, 실제 급여와 다름
    current_salary_signal = _estimate_annual_salary_signal(current_company)
    target_salary_signal = _estimate_annual_salary_signal(target_company)
    salary_change_signal = target_salary_signal - current_salary_signal
    salary_adjustment = _salary_diff_score_adjustment(salary_change_signal)

    adjusted_diff = diff + role_fit_delta * 2 + salary_adjustment
    score = _recommendation_score(adjusted_diff)
    verdict = _verdict_for(adjusted_diff)

    summary = {
        "total_diff": diff,
        "adjusted_diff": adjusted_diff,
        "growth_diff": target.growth - current.growth,
        "stability_diff": target.stability - current.stability,
        "size_fit_diff": target.size_fit - current.size_fit,
        "risk_penalty_diff": target.risk_penalty - current.risk_penalty,
        "role": role,
        "current_role_fit": current_role_fit,
        "target_role_fit": target_role_fit,
        "role_fit_delta": role_fit_delta,
        "salary_adjustment": salary_adjustment,
        "current_grade": current.grade,
        "target_grade": target.grade,
        "current_estimated_annual_salary_signal": current_salary_signal,
        "target_estimated_annual_salary_signal": target_salary_signal,
        "salary_change_note": (
            "국민연금 고지금액과 직원 수 기반 1인당 연봉 참고값 — 실제 급여 변화와 다름"
        ),
    }

    return RecommendationResult(
        score=score,
        current_company=current,
        target_company=target,
        salary_change_signal=salary_change_signal,
        role_fit_delta=role_fit_delta,
        summary=summary,
        verdict=verdict,
    )


def recommend_from_raw(
    current_company: Company,
    current_stats: Optional[Iterable[CompanyMonthlyStats]],
    target_company: Company,
    target_stats: Optional[Iterable[CompanyMonthlyStats]],
    role: str | None = None,
) -> RecommendationResult:
    """원천 데이터(Company + 월별 통계)로 건강도 계산부터 추천까지 한 번에 수행."""
    current = calculate_health_score(current_company, current_stats)
    target = calculate_health_score(target_company, target_stats)
    return calculate_recommendation(
        current, target, current_company, target_company, role
    )
