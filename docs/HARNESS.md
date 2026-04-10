# HARNESS.md — 하네스 설계 결정 기록

## 참고 문서

[Anthropic Engineering: Harness Design for Long-Running Apps](https://www.anthropic.com/engineering/harness-design-long-running-apps)

## 적용 원칙

### 원문 핵심 → 이 프로젝트 적용

| 원문 원칙 | 이 프로젝트 적용 |
|-----------|----------------|
| Generator-Evaluator 분리 | Sprint Contract로 구현/검증 역할 명확히 분리 |
| 파일 기반 통신 | `docs/sprint_current.md`로 에이전트 간 상태 전달 |
| Sprint 단위 작업 | 라우터 하나씩 구현 후 PASS 확인 후 커밋 |
| 컨텍스트 관리 | Sprint 완료 시 새 대화 권장 |
| 모델 개선 → 하네스 단순화 | 현재 Opus 4.6 기준으로 Sprint 구조 최소화 |

## 하네스 구성 요소

### 1. CLAUDE.md
Claude가 모든 대화 시작 시 읽는 프로젝트 컨텍스트.
- 코딩 규칙, 디렉토리 구조, 3-Agent 워크플로우 정의
- Sprint Contract 형식 포함

### 2. .claude/settings.json (Hooks)
Claude가 파일을 쓰거나 수정할 때 자동으로 실행되는 명령어.

| Hook | 시점 | 동작 |
|------|------|------|
| `PostToolUse(Write\|Edit)` | Python 파일 저장 후 | `ruff check --fix` + `ruff format` |
| `PreToolUse(Bash)` | Bash 명령 실행 전 | 명령어 로깅 |

### 3. docs/sprint_current.md
현재 진행 중인 Sprint의 Contract + 진행 상태.
Generator와 Evaluator가 이 파일을 통해 상태를 공유.

## 백엔드 전용 조정사항

원문은 프론트엔드 중심(Playwright로 UI 검증)이지만,
이 프로젝트는 순수 백엔드이므로 Evaluator를 다음으로 대체:

- **Playwright → pytest + httpx TestClient**
- UI 평가 기준 → API 평가 기준 (상태코드, 응답 구조, 엣지케이스)

## 권장 작업 흐름

```
새 기능 요청
    ↓
[Planner] docs/PRD.md 확인 → Sprint Contract 작성
    ↓
[Generator] 모델 → 스키마 → 라우터 → 테스트 구현
            (파일 저장마다 ruff 자동 실행)
    ↓
[Evaluator] pytest 실행 → Contract 체크리스트 검증
    ↓
PASS → git commit → 새 Sprint or 새 대화
FAIL → Generator에게 피드백 → 재구현
```

## 결정: Sprint 구조 최소화

원문에서 언급: "모델이 개선될수록 하네스를 단순화해야 합니다."

현재 Claude Sonnet 4.6 기준으로:
- ~~Sprint별 컨텍스트 리셋~~ → 필요 시에만
- ~~엄격한 Sprint 경계~~ → 라우터 단위로 자연스럽게 구분
- Evaluator는 반드시 별도 실행 유지 (자체 평가 편향 방지)
