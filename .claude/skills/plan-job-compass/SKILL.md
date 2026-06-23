---
name: plan-job-compass
description: >
  AI 이직 나침반 서비스 기획 워크플로우를 조율하는 오케스트레이터.
  기획, 설계, 스펙 작성, 문서화, 아키텍처, PRD, 사용자 스토리 요청 시 이 스킬을 반드시 사용할 것.
  구현 전 단계에서 제품 기획(PRD·사용자 스토리)과 기술 설계(아키텍처·API 스펙·DB 스키마)를 순차적으로 작성한다.
  "기획 다시", "스펙 업데이트", "설계 수정", "특정 문서만 다시" 요청에도 이 스킬을 사용할 것.
  단순 질문은 직접 응답 가능.
---

## 개요

AI 이직 나침반 서비스 기획을 2개의 서브 에이전트 파이프라인으로 수행한다.
산출물은 `docs/` 하위에 저장되며, build 단계(`build-job-compass`)에서 참조한다.

**실행 모드:** 서브 에이전트 (순차 파이프라인)
**에이전트 순서:** product-planner → tech-architect

---

## Phase 0: 컨텍스트 확인

기존 기획 문서 존재 여부를 확인하여 실행 모드를 결정한다.

```
확인 경로:
- docs/product/prd.md
- docs/product/user-stories.md
- docs/tech/architecture.md
- docs/tech/api-spec.md
- docs/tech/db-schema.md
```

| 상황 | 실행 모드 |
|------|----------|
| 문서 없음 | **초기 실행** — Phase 1부터 전체 실행 |
| 문서 있음 + 전체 재기획 요청 | **새 실행** — 기존 문서 백업 후 전체 실행 |
| 문서 있음 + 특정 문서만 수정 | **부분 재실행** — 해당 에이전트만 재호출 |

---

## Phase 1: 제품 기획

`product-planner` 에이전트를 호출하여 PRD와 사용자 스토리를 작성한다.

**에이전트 호출:**
```python
Agent(
    description="제품 기획 문서 작성",
    subagent_type="claude",
    model="opus",
    prompt="""
    [에이전트 정의: .claude/agents/product-planner.md 참조]

    컨텍스트:
    - README.md를 읽어 현재 기능 아이디어 파악
    - 포트폴리오/학습 목적 서비스임을 전제

    작업:
    1. docs/product/prd.md 작성
       - 서비스 목표 및 타깃 사용자
       - 기능 목록 및 우선순위 (MVP vs 이후)
       - 기능별 수용 기준
    2. docs/product/user-stories.md 작성
       - 이직 고민 중인 직장인 관점
       - 핵심 시나리오 3-5개

    완료 후 다음을 반환:
    - MVP 핵심 기능 목록 (3-5개)
    - 각 기능의 우선순위
    """
)
```

---

## Phase 2: 기술 설계

Phase 1 결과를 받아 `tech-architect` 에이전트를 호출한다.

**에이전트 호출:**
```python
Agent(
    description="기술 아키텍처 및 스펙 설계",
    subagent_type="claude",
    model="opus",
    prompt="""
    [에이전트 정의: .claude/agents/tech-architect.md 참조]

    Phase 1 산출물:
    {phase1_result}

    컨텍스트:
    - scripts/test_nps_api.py를 읽어 API 응답 필드 구조 파악
    - 기존 기술 스택: Python, NPS 공공 API

    작업:
    1. docs/tech/architecture.md
       - 기술 스택 선정 (FastAPI, SQLite, Anthropic SDK 등)
       - 컴포넌트 구성도 (텍스트 다이어그램)
       - 데이터 흐름
    2. docs/tech/api-spec.md
       - 엔드포인트별 요청/응답 스키마
    3. docs/tech/db-schema.md
       - 테이블 정의 + NPS 필드 매핑 테이블

    완료 후 핵심 설계 결정사항 요약을 반환한다.
    """
)
```

---

## Phase 3: 기획 완료 보고

모든 산출물 생성 후 현황을 정리한다.

체크리스트:
- [ ] `docs/product/prd.md` — MVP 범위 명확히 정의됨
- [ ] `docs/product/user-stories.md` — 사용자 스토리 3개 이상
- [ ] `docs/tech/architecture.md` — 기술 스택 + 데이터 흐름 포함
- [ ] `docs/tech/api-spec.md` — 3개 이상 엔드포인트 정의
- [ ] `docs/tech/db-schema.md` — NPS 필드 매핑 포함

완료 후 사용자에게 안내:
- 생성된 문서 목록
- 다음 단계: `build-job-compass` 스킬로 실제 구현 시작 가능

---

## 에러 핸들링

| 상황 | 대응 |
|------|------|
| 에이전트 실행 실패 | 1회 재시도. 재실패 시 해당 Phase 건너뛰고 진행, 최종 보고에 누락 명시 |
| README.md 없음 | 기억된 프로젝트 컨텍스트(국민연금 이직 추천 서비스)로 기획 진행 |

---

## 테스트 시나리오

**정상 흐름:**
```
"서비스 기획해줘"
→ Phase 0: 초기 실행 감지
→ Phase 1: PRD + 사용자 스토리 작성
→ Phase 2: 아키텍처 + API 스펙 + DB 스키마 설계
→ Phase 3: 문서 목록 보고 + 다음 단계 안내
```

**부분 재실행:**
```
"DB 스키마 설계만 다시 해줘"
→ Phase 0: 기존 문서 확인
→ Phase 2만 재실행 (product-planner 결과 재활용)
```
