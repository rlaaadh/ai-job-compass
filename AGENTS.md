# GPT Harness Bridge

이 프로젝트에서 GPT/Codex 계열 에이전트는 `.claude/` 하네스 구조를 기준으로 작업한다.
`.claude`가 소스 오브 트루스이며, 이 파일은 그 구조를 GPT가 이해하기 쉬운 규약으로 매핑한다.

## Project Goal

국민연금 공공 API 기반 기업 건강도 및 이직 추천도 서비스를 개발한다.

## Routing Rules

- 기획, 설계, 스펙, 문서화 요청이면 `.claude/skills/plan-job-compass/SKILL.md`를 우선 읽고 그 흐름을 따른다.
- 구현, 개발, 수정, 빌드 요청이면 `.claude/skills/build-job-compass/SKILL.md`를 우선 읽고 그 흐름을 따른다.
- 단순 질문, 짧은 설명, 작은 사실 확인은 직접 응답 가능하다.

## Planning Harness

기획 작업은 아래 순서의 파이프라인으로 이해한다.

1. `product-planner`
2. `tech-architect`

참조 파일:

- `.claude/agents/product-planner.md`
- `.claude/agents/tech-architect.md`

주요 산출물:

- `docs/product/prd.md`
- `docs/product/user-stories.md`
- `docs/tech/architecture.md`
- `docs/tech/api-spec.md`
- `docs/tech/db-schema.md`

## Build Harness

구현 작업은 아래 순서의 파이프라인으로 이해한다.

1. `data-pipeline`
2. `score-engine`
3. `ai-analyst`
4. `backend`

참조 파일:

- `.claude/agents/data-pipeline.md`
- `.claude/agents/score-engine.md`
- `.claude/agents/ai-analyst.md`
- `.claude/agents/backend.md`

주요 구현 대상:

- `data/raw/`
- `src/db/`
- `src/pipeline/`
- `src/scoring/`
- `src/ai/`
- `src/api/`
- `src/main.py`

## Working Rules

- 작업 전 관련 `.claude/skills/*.md`와 `.claude/agents/*.md`를 먼저 읽고 현재 요청에 맞는 단계만 수행한다.
- 기존 산출물이 있으면 재작성보다 수정과 확장을 우선한다.
- MVP 우선 원칙을 유지한다.
- `당월고지금액`은 정확한 급여가 아니라 참고 신호라는 점을 문서, 스키마, 코드에서 일관되게 유지한다.
- AI는 점수 계산이 아니라 점수 해석에만 사용한다.

## Notes

- 시각적 구조 설명이 필요하면 `docs/harness-overview.html`을 참고한다.
- Claude 전용 파일을 제거하지 말고, GPT/Codex 설정은 이 브리지 파일에서만 추가로 관리한다.
