from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class HealthScoreResult:
    """기업 건강도 점수 결과 (100점 만점).

    각 세부 항목 점수와 계산 근거(breakdown)를 함께 담는다.
    breakdown은 ai-analyst 에이전트가 자연어 해석에 활용한다.
    """

    total: int                       # 0-100 (세부 합산 후 0~100 clamp)
    growth: int                      # 성장성 점수 (0-35)
    stability: int                   # 안정성 점수 (0-30)
    hiring_activity: int             # 채용 활성도 점수 (0-15)
    size_fit: int                    # 규모 적합성 점수 (0-10)
    salary_signal: int               # 연봉 추정 점수 (0-10) — 당월고지금액 참고값
    risk_penalty: int                # 리스크 패널티 (0 이하, 감점)
    breakdown: dict = field(default_factory=dict)  # 각 항목 계산 근거
    grade: str = "보통"              # "매우 좋음"/"좋음"/"보통"/"주의"/"위험"


@dataclass
class RecommendationResult:
    """이직 추천도 결과.

    현재 회사와 관심(타겟) 회사의 HealthScoreResult를 비교한 결과다.
    summary는 ai-analyst가 비교 해석에 활용한다.
    """

    score: int                       # 0-100 (이직 추천 점수)
    current_company: HealthScoreResult
    target_company: HealthScoreResult
    salary_change_signal: int        # 연봉 변화 추정 (참고값, 실제 급여 아님)
    role_fit_delta: int = 0          # 직무 적합도 차이 (target - current)
    summary: dict = field(default_factory=dict)    # 비교 근거 요약
    verdict: str = "중립"            # "강력 추천"/"추천"/"중립"/"비추천"
