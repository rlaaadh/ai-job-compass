from __future__ import annotations

from typing import Iterable, Optional, Sequence

from src.db.models import Company, CompanyMonthlyStats
from src.scoring.schemas import HealthScoreResult

# 배점 상한
MAX_GROWTH = 40
MAX_STABILITY = 35
MAX_SIZE_FIT = 25
MAX_SALARY_SIGNAL = 10


def _clamp(value: float, low: float, high: float) -> int:
    return int(round(max(low, min(high, value))))


def _safe_int(value: Optional[int]) -> int:
    """None을 0으로 안전 변환."""
    return int(value) if value is not None else 0


def _estimate_annual_salary_signal(company: Optional[Company]) -> int:
    """국민연금 고지금액으로 1인당 연봉 참고값을 거칠게 추정한다."""
    if company is None:
        return 0

    charge = _safe_int(company.monthly_charge_amt)
    emp = _safe_int(company.employee_count)
    if charge <= 0 or emp <= 0:
        return 0

    per_capita_charge = charge / emp
    estimated_monthly_income = per_capita_charge / 0.09
    return int(round(estimated_monthly_income * 12))


def _sorted_stats(
    monthly_stats: Optional[Iterable[CompanyMonthlyStats]],
) -> list[CompanyMonthlyStats]:
    """year_month 오름차순 정렬, 최근 12개월만 사용. None 안전 처리."""
    if not monthly_stats:
        return []
    stats = [s for s in monthly_stats if s is not None and s.year_month]
    stats.sort(key=lambda s: s.year_month)
    return stats[-12:]


def _grade_for(total: int) -> str:
    if total >= 80:
        return "매우 좋음"
    if total >= 65:
        return "좋음"
    if total >= 45:
        return "보통"
    if total >= 30:
        return "주의"
    return "위험"


# ---------------------------------------------------------------------------
# 세부 항목 (각각 독립 함수 — 단위 테스트 가능)
# ---------------------------------------------------------------------------


def score_growth(
    stats: Sequence[CompanyMonthlyStats],
    company: Company,
) -> tuple[int, dict]:
    """성장성 (0-40): 전체 직원 수 증감률 + 최근 흐름."""
    detail: dict = {"max": MAX_GROWTH}

    if len(stats) < 2:
        # 부분 점수: 변동 데이터 없음 → 중립 절반 점수
        partial = MAX_GROWTH // 2
        detail.update(
            reason="월별 통계 부족 — 중립 점수 적용",
            employee_growth_pct=None,
            recent_trend_pct=None,
        )
        return partial, detail

    first = _safe_int(stats[0].employee_count)
    last = _safe_int(stats[-1].employee_count)
    growth_pct = ((last - first) / first * 100) if first > 0 else 0.0

    recent_start = _safe_int(stats[-4].employee_count) if len(stats) >= 4 else first
    if recent_start > 0:
        recent_trend_pct = ((last - recent_start) / recent_start) * 100
    else:
        recent_trend_pct = growth_pct

    growth_part = _clamp((growth_pct + 10) / 40 * 25, 0, 25)
    trend_part = _clamp((recent_trend_pct + 5) / 20 * 15, 0, 15)

    score = _clamp(growth_part + trend_part, 0, MAX_GROWTH)
    detail.update(
        reason="직원 수 증감률 + 최근 직원 수 흐름",
        employee_growth_pct=round(growth_pct, 1),
        recent_trend_pct=round(recent_trend_pct, 1),
        growth_part=growth_part,
        trend_part=trend_part,
    )
    return score, detail


def score_stability(stats: Sequence[CompanyMonthlyStats]) -> tuple[int, dict]:
    """안정성 (0-35): 이직률 + 월별 변동 안정성 + 최근 감소 방어력."""
    detail: dict = {"max": MAX_STABILITY}

    if len(stats) < 2:
        partial = MAX_STABILITY // 2
        detail.update(reason="월별 통계 부족 — 중립 점수 적용", turnover_rate=None)
        return partial, detail

    counts = [_safe_int(s.employee_count) for s in stats]
    avg_count = sum(counts) / len(counts) if counts else 0
    total_leavers = sum(_safe_int(s.leavers) for s in stats)
    # 연환산 이직률
    turnover_rate = (total_leavers / avg_count) if avg_count > 0 else 1.0

    turnover_part = _clamp((1 - min(turnover_rate, 0.5) / 0.5) * 20, 0, 20)

    # 월별 변동 안정성 (최대 10): 직원 수 변동계수가 작을수록 높음
    if avg_count > 0:
        variance = sum((c - avg_count) ** 2 for c in counts) / len(counts)
        std = variance ** 0.5
        cv = std / avg_count  # 변동계수
    else:
        cv = 1.0
    stability_part = _clamp((1 - min(cv, 0.3) / 0.3) * 10, 0, 10)

    if len(counts) >= 4:
        recent_counts = counts[-4:]
        decline_months = sum(
            1 for i in range(len(recent_counts) - 1) if recent_counts[i + 1] < recent_counts[i]
        )
        recent_defense_part = _clamp((3 - decline_months) / 3 * 5, 0, 5)
    else:
        recent_defense_part = 2

    score = _clamp(turnover_part + stability_part + recent_defense_part, 0, MAX_STABILITY)
    detail.update(
        reason="이직률 + 월별 직원 수 변동 안정성 + 최근 감소 방어력",
        turnover_rate=round(turnover_rate, 3),
        coefficient_of_variation=round(cv, 3),
        recent_defense_part=recent_defense_part,
    )
    return score, detail


def score_size_fit(
    stats: Sequence[CompanyMonthlyStats],
    company: Company,
) -> tuple[int, dict]:
    """기업 규모 (0-25): companies 테이블의 현재 직원 수만 반영."""
    detail: dict = {"max": MAX_SIZE_FIT}

    emp = _safe_int(company.employee_count)

    if emp >= 1_000:
        score = 25
    elif emp >= 500:
        score = 22
    elif emp >= 300:
        score = 19
    elif emp >= 100:
        score = 15
    elif emp >= 50:
        score = 11
    elif emp >= 30:
        score = 8
    elif emp >= 10:
        score = 4
    elif emp > 0:
        score = 1
    else:
        score = 0

    detail.update(
        reason="국민연금 가입 직원 수 구간",
        employee_count=emp,
        size_band_score=score,
    )
    return score, detail


def score_salary_signal(company: Company) -> tuple[int, dict]:
    """연봉 추정 참고 신호 (0-10): 총점에는 미반영, 건강도 해석용 보조 지표."""
    detail: dict = {"max": MAX_SALARY_SIGNAL}
    estimated_annual_salary = _estimate_annual_salary_signal(company)

    if estimated_annual_salary >= 90_000_000:
        score = 10
    elif estimated_annual_salary >= 75_000_000:
        score = 8
    elif estimated_annual_salary >= 60_000_000:
        score = 6
    elif estimated_annual_salary >= 45_000_000:
        score = 4
    elif estimated_annual_salary >= 35_000_000:
        score = 2
    elif estimated_annual_salary > 0:
        score = 1
    else:
        score = 0

    detail.update(
        reason="국민연금 고지금액 기반 1인당 연봉 추정 참고 신호",
        estimated_annual_salary=estimated_annual_salary or None,
        included_in_total=False,
        salary_band_score=score,
    )
    return score, detail


def score_risk_penalty(stats: Sequence[CompanyMonthlyStats]) -> tuple[int, dict]:
    """리스크 패널티 (<= 0): 최근 3개월 연속 감소 -10, 급격한 감소(>20%) -15."""
    detail: dict = {"reasons": []}
    penalty = 0

    if len(stats) >= 4:
        recent = stats[-4:]
        counts = [_safe_int(s.employee_count) for s in recent]
        # 최근 3개월 연속 감소 여부
        consecutive_down = all(
            counts[i + 1] < counts[i] for i in range(len(counts) - 1)
        )
        if consecutive_down:
            penalty -= 10
            detail["reasons"].append("최근 3개월 연속 직원 수 감소 (-10)")

    if len(stats) >= 2:
        recent = stats[-4:] if len(stats) >= 4 else stats
        start = _safe_int(recent[0].employee_count)
        end = _safe_int(recent[-1].employee_count)
        if start > 0:
            drop_pct = (start - end) / start * 100
            if drop_pct > 20:
                penalty -= 15
                detail["reasons"].append(
                    f"급격한 인원 감소 {round(drop_pct, 1)}% (-15)"
                )

    detail["penalty"] = penalty
    return penalty, detail


# ---------------------------------------------------------------------------
# 메인 진입점
# ---------------------------------------------------------------------------


def calculate_health_score(
    company: Company,
    monthly_stats: Optional[Iterable[CompanyMonthlyStats]] = None,
) -> HealthScoreResult:
    """Company와 최근 12개월 CompanyMonthlyStats로 건강도 점수를 계산한다.

    monthly_stats가 없거나 None이면 employee_count 기반으로 부분 점수를 반환한다
    (None 안전 처리).
    """
    stats = _sorted_stats(monthly_stats)

    growth, growth_d = score_growth(stats, company)
    stability, stability_d = score_stability(stats)
    size_fit, size_d = score_size_fit(stats, company)
    salary_signal, salary_d = score_salary_signal(company)
    penalty, penalty_d = score_risk_penalty(stats)

    positive_total = growth + stability + size_fit
    raw_total = positive_total + penalty
    total = _clamp(raw_total, 0, 100)
    grade = _grade_for(total)

    breakdown = {
        "growth": growth_d,
        "stability": stability_d,
        "size_fit": size_d,
        "salary_signal": salary_d,
        "risk_penalty": penalty_d,
        "months_available": len(stats),
        "has_monthly_stats": bool(stats),
        "raw_total_before_clamp": raw_total,
    }

    return HealthScoreResult(
        total=total,
        growth=growth,
        stability=stability,
        hiring_activity=0,
        size_fit=size_fit,
        salary_signal=salary_signal,
        risk_penalty=penalty,
        breakdown=breakdown,
        grade=grade,
    )
