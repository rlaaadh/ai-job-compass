---
name: build-job-compass
description: >
  이직각 서비스 전체 개발 워크플로우를 조율하는 오케스트레이터.
  서비스 구현, 개발, 빌드, 구축, 코딩 요청 시 이 스킬을 반드시 사용할 것.
  데이터 파이프라인 구현, 점수 엔진 개발, AI 분석 통합, FastAPI 백엔드 구현을 순차적으로 빌드한다.
  "다시 실행", "재실행", "업데이트", "수정", "특정 부분만 다시", "이전 결과 기반으로" 요청에도 이 스킬을 사용할 것.
  단순 질문이나 코드 설명 요청은 직접 응답 가능.
---

## 개요

이직각 서비스를 4개의 서브 에이전트 파이프라인으로 구축한다.

**실행 모드:** 서브 에이전트 (순차 파이프라인)
**에이전트 순서:** data-pipeline → score-engine → ai-analyst → backend

각 에이전트는 이전 에이전트의 산출물을 인계받아 자신의 영역을 구현하고, 다음 에이전트에게 필요한 인터페이스 정보를 전달한다.

---

## Phase 0: 컨텍스트 확인

워크플로우 시작 전 기존 산출물 존재 여부를 확인하여 실행 모드를 결정한다.

```
확인 경로:
- data/raw/
- src/db/
- src/pipeline/
- src/scoring/
- src/ai/
- src/
```

| 상황 | 실행 모드 |
|------|----------|
| 산출물 없음 | **초기 실행** — Phase 1부터 전체 실행 |
| 산출물 있음 + 전체 재실행 요청 | **새 실행** — 기존 산출물을 `_workspace_prev/`로 이동 후 전체 실행 |
| 산출물 있음 + 부분 수정 요청 | **부분 재실행** — 해당 에이전트만 재호출 |

---

## Phase 1: 데이터 파이프라인 구축

`data-pipeline` 에이전트를 호출하여 NPS API 클라이언트와 DB 스키마를 구현한다.

**에이전트 호출:**
```python
Agent(
    description="NPS 데이터 파이프라인 구현",
    subagent_type="claude",
    model="opus",
    prompt="""
    [에이전트 정의: .claude/agents/data-pipeline.md 참조]

    작업:
    1. data/raw/ 에 샘플 응답 3종 저장
       - establishment-basic (카카오 검색)
       - establishment-detail (seq로 상세 조회)
       - establishment-period (월별 통계)
    2. 실제 API 응답 구조를 기반으로 src/db/schema.sql 설계
    3. src/db/models.py SQLAlchemy 모델 구현
    4. scripts/test_nps_api.py를 src/pipeline/nps_client.py 클래스로 리팩토링
    5. src/pipeline/etl.py 기본 ETL 구현

    완료 후 다음을 반환:
    - src/db/models.py의 모델 구조 요약
    - src/pipeline/nps_client.py의 주요 메서드 인터페이스
    """
)
```

---

## Phase 2: 점수 엔진 구현

Phase 1 결과를 받아 `score-engine` 에이전트를 호출한다.

**에이전트 호출:**
```python
Agent(
    description="기업 건강도 & 이직 추천도 점수 엔진 구현",
    subagent_type="claude",
    model="opus",
    prompt="""
    [에이전트 정의: .claude/agents/score-engine.md 참조]

    Phase 1 산출물:
    {phase1_result}

    작업:
    1. src/scoring/health_score.py — 기업 건강도 점수 계산 (100점 만점)
       - 성장성 35 + 안정성 30 + 채용활성도 15 + 규모적합성 10 + 연봉추정 10 - 리스크패널티
    2. src/scoring/recommendation.py — 이직 추천도 계산
    3. src/scoring/schemas.py — 결과 데이터 구조 (Pydantic 또는 dataclass)
    4. src/scoring/tests/ — 점수 계산 단위 테스트

    완료 후 다음을 반환:
    - src/scoring/schemas.py의 결과 스키마 구조
    - 주요 함수 인터페이스 요약
    """
)
```

---

## Phase 3: AI 분석 통합

Phase 1-2 결과를 받아 `ai-analyst` 에이전트를 호출한다.

**에이전트 호출:**
```python
Agent(
    description="Claude AI 자연어 분석 리포트 통합",
    subagent_type="claude",
    model="opus",
    prompt="""
    [에이전트 정의: .claude/agents/ai-analyst.md 참조]

    Phase 2 산출물:
    {phase2_result}

    작업:
    1. src/ai/prompts.py — 프롬프트 템플릿
       - 기업 건강도 해석용 프롬프트
       - 이직 추천도 해석용 프롬프트
    2. src/ai/report_generator.py — Claude API 통합
       - 모델: claude-haiku-4-5-20251001
       - API 키: ANTHROPIC_API_KEY 환경변수
    3. src/ai/schemas.py — 리포트 출력 구조

    AI는 점수 계산이 아니라 "왜 이 점수인지 설명"에만 사용한다.

    완료 후 다음을 반환:
    - src/ai/report_generator.py의 주요 함수 인터페이스
    - 리포트 출력 스키마 구조
    """
)
```

---

## Phase 4: 백엔드 서버 구현

Phase 1-3 결과를 모두 받아 `backend` 에이전트를 호출한다.

**에이전트 호출:**
```python
Agent(
    description="FastAPI 백엔드 서버 구현",
    subagent_type="claude",
    model="opus",
    prompt="""
    [에이전트 정의: .claude/agents/backend.md 참조]

    Phase 1-3 산출물:
    {phase1_result}
    {phase2_result}
    {phase3_result}

    작업:
    1. src/main.py — FastAPI 앱 (CORS 포함)
    2. src/api/routers/company.py — /companies/search, /companies/{seq}/health
    3. src/api/routers/comparison.py — /compare
    4. src/api/schemas.py — Pydantic 요청/응답 모델
    5. requirements.txt — 전체 의존성
    6. README.md 업데이트 — 실행 방법 + API 문서 URL

    완료 후 서버 실행 커맨드와 API 테스트 방법을 반환한다.
    """
)
```

---

## Phase 5: 최종 검증

모든 에이전트 완료 후 구조를 확인한다.

체크리스트:
- [ ] `data/raw/` — 샘플 JSON 3종 존재
- [ ] `src/db/schema.sql` + `src/db/models.py` 존재
- [ ] `src/pipeline/nps_client.py` 존재
- [ ] `src/scoring/` — health_score.py + recommendation.py + schemas.py 존재
- [ ] `src/ai/` — report_generator.py + prompts.py 존재
- [ ] `src/main.py` + `src/api/` 존재
- [ ] `requirements.txt` 존재
- [ ] `.env.example` — ANTHROPIC_API_KEY 추가 여부 확인

---

## 에러 핸들링

| 상황 | 대응 |
|------|------|
| 에이전트 실행 실패 | 1회 재시도. 재실패 시 해당 Phase를 건너뛰고 진행, 최종 보고에 누락 명시 |
| NPS API 연결 불가 | 기존 `data/raw/` 샘플 데이터로 대체하여 이후 Phase 계속 |
| ANTHROPIC_API_KEY 미설정 | Phase 3을 건너뛰고 Phase 4 진행, 백엔드에 AI 분석 없이 배포 가능하게 구현 |

---

## 테스트 시나리오

**정상 흐름:**
```
"서비스 개발 시작해줘"
→ Phase 0: 초기 실행 감지
→ Phase 1-4 순차 실행
→ Phase 5: 체크리스트 확인
→ 실행 커맨드 안내
```

**부분 재실행:**
```
"점수 엔진만 다시 수정해줘"
→ Phase 0: 기존 산출물 확인
→ Phase 2만 재실행 (data-pipeline 결과 재활용)
→ Phase 3, 4 영향 여부 검토
```

**에러 흐름:**
```
ANTHROPIC_API_KEY 미설정
→ Phase 3 건너뜀
→ Phase 4: AI 분석 없이 점수만 반환하는 백엔드 구현
→ 최종 보고에 AI 기능 비활성화 명시
```
