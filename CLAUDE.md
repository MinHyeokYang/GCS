# CLAUDE.md — Team Todo API Harness

## Project Overview

팀 단위 Todo 관리 백엔드. Python + FastAPI + SQLAlchemy + SQLite.
설계 문서: `docs/PRD.md`, `docs/TSD.md`, `docs/DATABASE.md`

## Tech Stack

- **Framework**: FastAPI (Swagger: `/docs`)
- **ORM**: SQLAlchemy 2.0
- **DB**: SQLite (`todo.db`)
- **Migration**: Alembic
- **Validation**: Pydantic v2

## Directory Structure

```
app/
  main.py        # 앱 진입점
  database.py    # DB 연결
  models.py      # SQLAlchemy 모델
  schemas.py     # Pydantic 스키마
  routers/
    users.py
    teams.py
    todos.py
    tags.py
tests/
  test_users.py
  test_teams.py
  test_todos.py
  test_tags.py
docs/
alembic/
```

## Coding Standards

- **Linter**: `ruff check --fix` (ALL rules, `pyproject.toml` 참고)
- **Formatter**: `ruff format`
- **Type checker**: `mypy --strict`
- 모든 함수에 타입 힌트 필수
- 모든 엔드포인트에 `response_model`, `summary`, `status_code` 필수
- Docstring: Google 스타일

## Harness: 3-Agent Workflow

### 1. Planner (기능 설계)
새 기능 요청 시 구현 전에 반드시:
1. `docs/PRD.md`의 요구사항 확인
2. 영향받는 모델/스키마/라우터 파악
3. Sprint Contract 작성 → `docs/sprint_current.md`에 저장

### 2. Generator (구현)
Sprint Contract 기반으로 한 번에 하나의 기능만 구현:
- 모델 → 스키마 → 라우터 → 테스트 순서 준수
- 각 파일 수정 후 ruff가 자동 실행됨 (hook)
- 구현 완료 시 `docs/sprint_current.md`에 결과 기록

### 3. Evaluator (검증)
Generator 완료 후 독립적으로 검증:
- `pytest tests/` 실행
- FastAPI TestClient로 엔드포인트 직접 호출
- Sprint Contract의 완료 기준과 대조
- 결과를 `docs/sprint_current.md`에 PASS/FAIL로 기록

## Sprint Contract 형식

`docs/sprint_current.md` 에 아래 형식으로 작성:

```markdown
## Sprint: <기능명>

### 구현 범위
- [ ] 모델 변경
- [ ] 스키마 추가
- [ ] 라우터 구현
- [ ] 테스트 작성

### 완료 기준 (Evaluator 체크리스트)
- [ ] POST /... → 201 반환
- [ ] GET /...  → 200 + 올바른 JSON 구조
- [ ] 존재하지 않는 리소스 → 404
- [ ] 유효성 오류 → 422

### 결과
- Generator: ...
- Evaluator: PASS / FAIL
```

## File-Based Communication

에이전트 간 상태는 파일로 전달:
- `docs/sprint_current.md`: 현재 Sprint 상태
- `docs/sprint_history/`: 완료된 Sprint 아카이브

## Key Rules

1. **구현 전 Contract 먼저** — 코드 작성 전 완료 기준 합의
2. **Sprint 단위 커밋** — 하나의 기능이 PASS 되면 커밋
3. **Evaluator는 Generator 코드를 수정하지 않음** — FAIL 시 Generator에게 피드백만
4. **컨텍스트 관리** — Sprint 완료 시 새 대화로 시작 권장
