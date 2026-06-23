from __future__ import annotations

import json

from src.scoring.schemas import HealthScoreResult, RecommendationResult

# AI에게 부여하는 공통 역할/지침. 점수 계산이 아닌 "해석"만 맡긴다.
SYSTEM_INSTRUCTION = (
    "당신은 국민연금 공공데이터 기반 기업 건강도 점수를 해석해주는 "
    "이직 분석가입니다. 점수는 이미 룰 기반으로 계산되어 주어집니다. "
    "당신의 역할은 점수를 다시 계산하는 것이 아니라, 주어진 점수와 근거가 "
    "'무엇을 의미하는지'를 이직을 고민하는 직장인이 이해하기 쉽게 "
    "자연스러운 한국어로 풀어 설명하는 것입니다. "
    "주어진 근거(breakdown)에 없는 수치를 지어내지 마세요. "
    "연봉 관련 수치는 국민연금 고지금액 기반 참고값이며 실제 급여와 "
    "다를 수 있다는 점을 반드시 명시하세요."
)


def _ko_json(data: dict) -> str:
    """딕셔너리를 한국어가 깨지지 않게 JSON 문자열로 직렬화."""
    return json.dumps(data, ensure_ascii=False, indent=2, default=str)


def build_company_prompt(score: HealthScoreResult, company_name: str) -> str:
    """기업 건강도 해석 요청 프롬프트.

    HealthScoreResult의 점수와 breakdown 딕셔너리를 전달해
    근거 기반 자연어 해석을 요청한다.
    """
    payload = {
        "회사명": company_name,
        "총점(0-100)": score.total,
        "등급": score.grade,
        "세부점수": {
            "성장성(0-35)": score.growth,
            "안정성(0-30)": score.stability,
            "채용활성도(0-15)": score.hiring_activity,
            "규모적합성(0-10)": score.size_fit,
            "연봉신호(0-10, 참고값)": score.salary_signal,
            "리스크패널티(감점)": score.risk_penalty,
        },
        "계산근거(breakdown)": score.breakdown,
    }

    return (
        f"다음은 '{company_name}' 기업의 건강도 점수와 계산 근거입니다.\n\n"
        f"{_ko_json(payload)}\n\n"
        "위 점수가 의미하는 바를 해석해 아래 JSON 형식으로만 답하세요. "
        "각 항목은 점수를 직접 다시 계산하지 말고, 주어진 점수와 근거가 "
        "이직을 고민하는 직장인에게 어떤 의미인지 자연스럽게 설명하세요.\n\n"
        "{\n"
        '  "summary": "기업 건강도 전반에 대한 2-3문장 요약",\n'
        '  "growth_comment": "성장성 점수와 근거에 대한 1-2문장 해석",\n'
        '  "stability_comment": "안정성 점수와 근거에 대한 1-2문장 해석",\n'
        '  "hiring_comment": "채용 활성도 점수와 근거에 대한 1-2문장 해석"\n'
        "}\n\n"
        "JSON 외의 다른 텍스트는 출력하지 마세요."
    )


def build_recommendation_prompt(
    rec: RecommendationResult, current_name: str, target_name: str
) -> str:
    """이직 추천 해석 요청 프롬프트.

    RecommendationResult의 summary 딕셔너리(두 회사 점수 차이와 근거)를
    전달해 종합 의견과 예상 리스크 해석을 요청한다.
    """
    payload = {
        "현재회사": current_name,
        "관심회사": target_name,
        "이직추천점수(0-100)": rec.score,
        "판정": rec.verdict,
        "연봉변화신호(참고값)": rec.salary_change_signal,
        "비교근거(summary)": rec.summary,
        "현재회사_총점": rec.current_company.total,
        "관심회사_총점": rec.target_company.total,
    }

    return (
        f"다음은 현재 회사 '{current_name}'와 관심 회사 '{target_name}'의 "
        "건강도 비교 결과입니다.\n\n"
        f"{_ko_json(payload)}\n\n"
        "두 회사의 점수 차이와 근거를 바탕으로 이직 추천 종합 의견을 "
        "해석해 아래 JSON 형식으로만 답하세요. 점수를 다시 계산하지 말고, "
        "주어진 비교 근거가 이직을 고민하는 직장인에게 어떤 의미인지 "
        "자연스럽게 설명하세요. 연봉 변화 신호는 국민연금 고지금액 기반 "
        "참고값이며 실제 급여 변화와 다를 수 있다는 점을 salary_comment에 "
        "반드시 포함하세요.\n\n"
        "{\n"
        '  "summary": "이직 추천에 대한 2-3문장 종합 의견",\n'
        '  "risk_comment": "예상되는 리스크에 대한 1-2문장 해석",\n'
        '  "salary_comment": "연봉 변화에 대한 1-2문장 해석 (참고값임을 명시)"\n'
        "}\n\n"
        "JSON 외의 다른 텍스트는 출력하지 마세요."
    )
