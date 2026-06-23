from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.ai.prompts import (
    SYSTEM_INSTRUCTION,
    build_company_prompt,
    build_recommendation_prompt,
)
from src.ai.schemas import CompanyReport, RecommendationReport
from src.scoring.schemas import HealthScoreResult, RecommendationResult

_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
# 비용 효율적이며 해석 태스크에 충분한 모델
_MODEL = "claude-haiku-4-5-20251001"
_MAX_TOKENS = 1024


def _load_api_key() -> Optional[str]:
    """ANTHROPIC_API_KEY를 환경변수 우선, 없으면 .env에서 로드.

    (nps_client._load_api_key 방식 참고. 단 키가 없어도 예외를 던지지 않고
    None을 반환해 fallback 모드로 동작하게 한다.)
    """
    env_key = os.environ.get("ANTHROPIC_API_KEY")
    if env_key:
        return env_key.strip().strip("\"'")

    if _ENV_FILE.exists():
        for line in _ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("ANTHROPIC_API_KEY="):
                value = line.split("=", 1)[1].strip().strip("\"'")
                # .env.example의 플레이스홀더는 무시
                if value and value != "your_anthropic_api_key_here":
                    return value
    return None


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _extract_json(text: str) -> dict:
    """모델 응답 텍스트에서 JSON 객체를 추출해 파싱.

    코드펜스(```json ... ```)나 앞뒤 잡텍스트가 있어도 첫 번째 {...} 블록을
    찾아 파싱한다. 실패하면 ValueError를 던진다.
    """
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        pass

    match = re.search(r"\{.*\}", text or "", re.DOTALL)
    if match:
        return json.loads(match.group(0))
    raise ValueError("응답에서 JSON을 찾을 수 없습니다.")


class ReportGenerator:
    """점수 결과를 Claude API로 자연어 리포트로 변환한다.

    API 키가 없거나 호출에 실패하면 기본 템플릿 텍스트를 반환해
    서비스가 중단되지 않게 한다 (fallback 모드).
    """

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or _load_api_key()
        self._client = None

        if self.api_key:
            try:
                import anthropic

                self._client = anthropic.Anthropic(api_key=self.api_key)
            except ImportError:
                # anthropic 패키지가 없으면 fallback 모드
                self._client = None

    @property
    def is_ai_enabled(self) -> bool:
        """실제 AI 호출이 가능한 상태인지 여부."""
        return self._client is not None

    # ------------------------------------------------------------------
    # 내부 호출 헬퍼
    # ------------------------------------------------------------------
    def _call(self, prompt: str) -> Optional[dict]:
        """Claude API를 호출해 JSON 딕셔너리를 반환. 실패 시 None."""
        if self._client is None:
            return None
        try:
            response = self._client.messages.create(
                model=_MODEL,
                max_tokens=_MAX_TOKENS,
                system=SYSTEM_INSTRUCTION,
                messages=[{"role": "user", "content": prompt}],
            )
            text = next(
                (b.text for b in response.content if b.type == "text"), ""
            )
            return _extract_json(text)
        except Exception:
            # 네트워크/인증/파싱 등 모든 오류 → fallback
            return None

    # ------------------------------------------------------------------
    # 기업 건강도 리포트
    # ------------------------------------------------------------------
    def generate_company_report(
        self, score: HealthScoreResult, company_name: str
    ) -> CompanyReport:
        prompt = build_company_prompt(score, company_name)
        data = self._call(prompt)

        if data:
            return CompanyReport(
                summary=str(data.get("summary") or "").strip()
                or self._fallback_company_summary(score, company_name),
                growth_comment=str(data.get("growth_comment") or "").strip()
                or self._fallback_growth(score),
                stability_comment=str(data.get("stability_comment") or "").strip()
                or self._fallback_stability(score),
                hiring_comment=str(data.get("hiring_comment") or "").strip()
                or self._fallback_hiring(score),
                generated_at=_now_iso(),
            )

        return self._fallback_company_report(score, company_name)

    # ------------------------------------------------------------------
    # 이직 추천 리포트
    # ------------------------------------------------------------------
    def generate_recommendation_report(
        self, rec: RecommendationResult, current_name: str, target_name: str
    ) -> RecommendationReport:
        prompt = build_recommendation_prompt(rec, current_name, target_name)
        data = self._call(prompt)

        if data:
            return RecommendationReport(
                summary=str(data.get("summary") or "").strip()
                or self._fallback_rec_summary(rec, current_name, target_name),
                risk_comment=str(data.get("risk_comment") or "").strip()
                or self._fallback_risk(rec),
                salary_comment=str(data.get("salary_comment") or "").strip()
                or self._fallback_salary(rec),
                generated_at=_now_iso(),
            )

        return self._fallback_recommendation_report(rec, current_name, target_name)

    # ------------------------------------------------------------------
    # Fallback 템플릿 (API 미사용/실패 시)
    # ------------------------------------------------------------------
    @staticmethod
    def _fallback_company_summary(score: HealthScoreResult, name: str) -> str:
        return (
            f"{name}의 기업 건강도는 100점 만점에 {score.total}점으로 "
            f"'{score.grade}' 수준입니다. 성장성 {score.growth}점, "
            f"안정성 {score.stability}점, 채용 활성도 {score.hiring_activity}점으로 "
            "구성되어 있습니다."
        )

    @staticmethod
    def _fallback_growth(score: HealthScoreResult) -> str:
        return f"성장성 점수는 35점 만점에 {score.growth}점입니다."

    @staticmethod
    def _fallback_stability(score: HealthScoreResult) -> str:
        return f"안정성 점수는 30점 만점에 {score.stability}점입니다."

    @staticmethod
    def _fallback_hiring(score: HealthScoreResult) -> str:
        return f"채용 활성도 점수는 15점 만점에 {score.hiring_activity}점입니다."

    def _fallback_company_report(
        self, score: HealthScoreResult, name: str
    ) -> CompanyReport:
        return CompanyReport(
            summary=self._fallback_company_summary(score, name),
            growth_comment=self._fallback_growth(score),
            stability_comment=self._fallback_stability(score),
            hiring_comment=self._fallback_hiring(score),
            generated_at=_now_iso(),
        )

    @staticmethod
    def _fallback_rec_summary(
        rec: RecommendationResult, current: str, target: str
    ) -> str:
        diff = rec.summary.get("total_diff", 0)
        direction = "높습니다" if diff > 0 else ("낮습니다" if diff < 0 else "비슷합니다")
        return (
            f"{current} 대비 {target}의 이직 추천 점수는 100점 만점에 "
            f"{rec.score}점으로 '{rec.verdict}'입니다. 관심 회사의 건강도가 "
            f"현재 회사보다 {abs(diff)}점 {direction}."
        )

    @staticmethod
    def _fallback_risk(rec: RecommendationResult) -> str:
        return (
            f"이직 판정은 '{rec.verdict}'입니다. 점수 차이와 각 항목 변화를 "
            "참고해 신중히 결정하세요."
        )

    @staticmethod
    def _fallback_salary(rec: RecommendationResult) -> str:
        return (
            f"연봉 변화 추정 신호는 {rec.salary_change_signal}입니다. "
            "이는 국민연금 고지금액 기반 참고값이며 실제 급여 변화와 "
            "다를 수 있습니다."
        )

    def _fallback_recommendation_report(
        self, rec: RecommendationResult, current: str, target: str
    ) -> RecommendationReport:
        return RecommendationReport(
            summary=self._fallback_rec_summary(rec, current, target),
            risk_comment=self._fallback_risk(rec),
            salary_comment=self._fallback_salary(rec),
            generated_at=_now_iso(),
        )
