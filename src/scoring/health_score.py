from __future__ import annotations

from typing import Iterable, Optional, Sequence

from src.db.models import Company, CompanyMonthlyStats
from src.scoring.schemas import HealthScoreResult

# 배점 상한
MAX_GROWTH = 35
MAX_STABILITY = 30
MAX_HIRING = 15
MAX_SIZE_FIT = 10
MAX_SALARY = 10


def _clamp(value: float, low: float, high: float) -> int:
    return int(round(max(low, min(high, value))))


def _safe_int(value: Optional[int]) -> int:
    """None을 0으로 안전 변환."""
    return int(value) if value is not None else 0


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
    """성장성 (0-35): 직원 수 증감률 + 입사자/퇴사자 비율."""
    detail: dict = {"max": MAX_GROWTH}

    if len(stats) < 2:
        # 부분 점수: 변동 데이터 없음 → 중립 절반 점수
        partial = MAX_GROWTH // 2
        detail.update(
            reason="월별 통계 부족 — 중립 점수 적용",
            employee_growth_pct=None,
            joiner_leaver_ratio=None,
        )
        return partial, detail

    first = _safe_int(stats[0].employee_count)
    last = _safe_int(stats[-1].employee_count)
    growth_pct = ((last - first) / first * 100) if first > 0 else 0.0

    total_joiners = sum(_safe_int(s.new_joiners) for s in stats)
    total_leavers = sum(_safe_int(s.leavers) for s in stats)
    # 입사자/퇴사자 비율 (퇴사자 0이면 입사자 있을 때 큰 값)
    if total_leavers > 0:
        ratio = total_joiners / total_leavers
    elif total_joiners > 0:
        ratio = 2.0
    else:
        ratio = 1.0

    # 증감률 점수 (최대 22): -10% ~ +30% 구간을 0~22로 매핑
    growth_part = _clamp((growth_pct + 10) / 40 * 22, 0, 22)
    # 입퇴사 비율 점수 (최대 13): ratio 0.5~1.5를 0~13으로 매핑
    ratio_part = _clamp((ratio - 0.5) / 1.0 * 13, 0, 13)

    score = _clamp(growth_part + ratio_part, 0, MAX_GROWTH)
    detail.update(
        reason="직원 수 증감률 + 입사자/퇴사자 비율",
        employee_growth_pct=round(growth_pct, 1),
        joiner_leaver_ratio=round(ratio, 2),
        total_joiners=total_joiners,
        total_leavers=total_leavers,
    )
    return score, detail


def score_stability(stats: Sequence[CompanyMonthlyStats]) -> tuple[int, dict]:
    """안정성 (0-30): 이직률(leavers / 평균 직원 수) + 월별 변동 안정성."""
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

    # 이직률 점수 (최대 18): 0%~50% 이직률을 18~0으로 역매핑
    turnover_part = _clamp((1 - min(turnover_rate, 0.5) / 0.5) * 18, 0, 18)

    # 월별 변동 안정성 (최대 12): 직원 수 변동계수가 작을수록 높음
    if avg_count > 0:
        variance = sum((c - avg_count) ** 2 for c in counts) / len(counts)
        std = variance ** 0.5
        cv = std / avg_count  # 변동계수
    else:
        cv = 1.0
    stability_part = _clamp((1 - min(cv, 0.3) / 0.3) * 12, 0, 12)

    score = _clamp(turnover_part + stability_part, 0, MAX_STABILITY)
    detail.update(
        reason="이직률 + 월별 직원 수 변동 안정성",
        turnover_rate=round(turnover_rate, 3),
        coefficient_of_variation=round(cv, 3),
    )
    return score, detail


def score_hiring_activity(stats: Sequence[CompanyMonthlyStats]) -> tuple[int, dict]:
    """채용 활성도 (0-15): 최근 3개월 신규 취득자 비율."""
    detail: dict = {"max": MAX_HIRING}

    if not stats:
        detail.update(reason="월별 통계 없음", recent_hire_ratio=None)
        return 0, detail

    recent = stats[-3:]
    recent_joiners = sum(_safe_int(s.new_joiners) for s in recent)
    base_count = _safe_int(recent[-1].employee_count)
    hire_ratio = (recent_joiners / base_count) if base_count > 0 else 0.0

    # 0%~15% 신규 비율을 0~15점으로 매핑
    score = _clamp(hire_ratio / 0.15 * MAX_HIRING, 0, MAX_HIRING)
    detail.update(
        reason="최근 3개월 신규 취득자 / 현재 직원 수",
        recent_joiners=recent_joiners,
        recent_hire_ratio=round(hire_ratio, 3),
        months_used=len(recent),
    )
    return score, detail


def score_size_fit(
    stats: Sequence[CompanyMonthlyStats],
    company: Company,
) -> tuple[int, dict]:
    """규모 적합성 (0-10): 직원 수 구간 + 성장 패턴 일관성."""
    detail: dict = {"max": MAX_SIZE_FIT}

    # 현재 직원 수: 최신 월별 통계 우선, 없으면 Company.employee_count
    if stats:
        emp = _safe_int(stats[-1].employee_count)
    else:
        emp = _safe_int(company.employee_count)

    # 구간별 기본 점수 (최대 6)
    if emp >= 300:
        size_base = 6
    elif emp >= 100:
        size_base = 6
    elif emp >= 30:
        size_base = 5
    elif emp >= 10:
        size_base = 4
    elif emp > 0:
        size_base = 3
    else:
        size_base = 0

    # 성장 패턴 일관성 (최대 4): 월별 증가 방향이 일관되면 가점
    consistency_part = 0
    consistent_ratio = None
    if len(stats) >= 3:
        diffs = [
            _safe_int(stats[i + 1].employee_count) - _safe_int(stats[i].employee_count)
            for i in range(len(stats) - 1)
        ]
        non_zero = [d for d in diffs if d != 0]
        if non_zero:
            ups = sum(1 for d in non_zero if d > 0)
            consistent_ratio = ups / len(non_zero)
            # 한 방향으로 일관될수록(0 또는 1에 가까울수록) 가점
            directionality = abs(consistent_ratio - 0.5) * 2  # 0~1
            consistency_part = _clamp(directionality * 4, 0, 4)
        else:
            consistency_part = 2  # 변동 없음 = 안정적
    elif emp > 0:
        consistency_part = 2  # 데이터 부족 시 중립

    score = _clamp(size_base + consistency_part, 0, MAX_SIZE_FIT)
    detail.update(
        reason="직원 수 구간 + 성장 패턴 일관성",
        employee_count=emp,
        size_base=size_base,
        growth_consistency_ratio=(
            round(consistent_ratio, 2) if consistent_ratio is not None else None
        ),
    )
    return score, detail


def score_salary_signal(company: Company) -> tuple[int, dict]:
    """연봉 추정 (0-10): 당월고지금액(monthly_charge_amt) 기반 — 참고값.

    국민연금 고지금액은 실제 임금과 다르므로 참고용 신호로만 사용한다.
    """
    detail: dict = {"max": MAX_SALARY, "is_reference_only": True}
    charge = company.monthly_charge_amt

    if not charge or charge <= 0:
        detail.update(
            reason="당월고지금액 없음 (참고값) — 중립 점수",
            monthly_charge_amt=charge,
            note="국민연금 고지금액 기반, 실제 급여와 다름",
        )
        return MAX_SALARY // 2, detail

    emp = _safe_int(company.employee_count)
    # 1인당 고지금액 추정 (참고값)
    per_capita = (charge / emp) if emp > 0 else charge

    # 1인당 0 ~ 300,000원 구간을 0~10으로 매핑 (참고용 단순 스케일)
    score = _clamp(per_capita / 300_000 * MAX_SALARY, 0, MAX_SALARY)
    detail.update(
        reason="당월고지금액 / 직원 수 (참고값)",
        monthly_charge_amt=charge,
        per_capita_charge=int(per_capita),
        note="국민연금 고지금액 기반 참고값 — 실제 급여와 다름",
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

    monthly_stats가 없거나 None이면 employee_count / monthly_charge_amt
    기반으로 부분 점수를 반환한다 (None 안전 처리).
    """
    stats = _sorted_stats(monthly_stats)

    growth, growth_d = score_growth(stats, company)
    stability, stability_d = score_stability(stats)
    hiring, hiring_d = score_hiring_activity(stats)
    size_fit, size_d = score_size_fit(stats, company)
    salary, salary_d = score_salary_signal(company)
    penalty, penalty_d = score_risk_penalty(stats)

    raw_total = growth + stability + hiring + size_fit + salary + penalty
    total = _clamp(raw_total, 0, 100)
    grade = _grade_for(total)

    breakdown = {
        "growth": growth_d,
        "stability": stability_d,
        "hiring_activity": hiring_d,
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
        hiring_activity=hiring,
        size_fit=size_fit,
        salary_signal=salary,
        risk_penalty=penalty,
        breakdown=breakdown,
        grade=grade,
    )
