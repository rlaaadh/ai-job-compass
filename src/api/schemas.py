from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class CompanyBasicResponse(BaseModel):
    seq: int
    name: str
    address: Optional[str] = None
    industry_name: Optional[str] = None
    employee_count: Optional[int] = None
    join_status: Optional[str] = None


class CompanyReportResponse(BaseModel):
    summary: str
    growth_comment: str
    stability_comment: str
    hiring_comment: str


class HealthScoreResponse(BaseModel):
    seq: int
    name: str
    health_score: int
    grade: str                   # 매우 좋음 / 좋음 / 보통 / 주의 / 위험
    growth: int
    stability: int
    hiring_activity: int
    breakdown: dict
    ai_report: Optional[CompanyReportResponse] = None  # AI 분석 없을 때 None


class CompareRequest(BaseModel):
    current_seq: int
    target_seq: int


class RecommendationReportResponse(BaseModel):
    summary: str
    risk_comment: str
    salary_comment: str


class CompareResponse(BaseModel):
    recommendation_score: int
    verdict: str                 # 강력 추천 / 추천 / 중립 / 비추천
    current: HealthScoreResponse
    target: HealthScoreResponse
    salary_change_signal: int    # 참고값
    ai_report: Optional[RecommendationReportResponse] = None


class ErrorResponse(BaseModel):
    detail: str
