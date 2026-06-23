from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CompanyReport:
    """기업 건강도 분석 리포트 (AI 자연어 해석).

    HealthScoreResult의 점수/breakdown을 사람이 이해하기 쉬운
    자연어로 풀어쓴 결과다. AI 호출 실패 시 기본 템플릿 텍스트가 담긴다.
    """

    summary: str              # 기업 건강도 자연어 요약 (2-3문장)
    growth_comment: str       # 성장성 해석
    stability_comment: str    # 안정성 해석
    hiring_comment: str       # 채용 활성도 해석
    generated_at: str         # ISO 타임스탬프


@dataclass
class RecommendationReport:
    """이직 추천 분석 리포트 (AI 자연어 해석).

    RecommendationResult의 비교 근거를 자연어 종합 의견으로 풀어쓴 결과다.
    AI 호출 실패 시 기본 템플릿 텍스트가 담긴다.
    """

    summary: str              # 이직 추천 종합 의견 (2-3문장)
    risk_comment: str         # 예상 리스크
    salary_comment: str       # 연봉 변화 해석 (참고값임을 포함)
    generated_at: str
