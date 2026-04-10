# Team Todo API

간단 사용법 중심 README — 팀 단위 Todo 관리 백엔드 (FastAPI + SQLAlchemy + SQLite)

언어: 한국어

## 빠른 시작

1. 의존성 설치

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .\.venv\Scripts\activate
pip install -r requirements.txt
```

2. 데이터베이스 마이그레이션

```bash
alembic upgrade head
```

3. 개발 서버 실행

```bash
uvicorn app.main:app --reload
```

4. API 문서 (Swagger)

브라우저에서: http://localhost:8000/docs

## 주요 엔드포인트 (요약)

- POST /users — 유저 생성
- GET /users — 유저 목록
- POST /teams — 팀 생성
- POST /teams/{team_id}/todos — Todo 생성
- GET /teams/{team_id}/todos — Todo 목록 조회 (status, priority, assignee, tag 필터)

자세한 API 명세는 docs/PRD.md 및 app/routers/*.py를 참조하세요.

## DB & 마이그레이션

- SQLite 파일: todo.db (프로젝트 루트)
- 마이그레이션 도구: Alembic (alembic/ 폴더)

## 테스트

```bash
pip install -r requirements-dev.txt
pytest tests/
```

## 개발 규칙

- Linter: ruff check --fix
- Formatter: ruff format
- Type checking: mypy --strict
- 모든 엔드포인트는 response_model, summary, status_code 명시

## 컨트리뷰팅 / 스프린트

- Sprint Contract 작성: docs/sprint_current.md
- Generator → Evaluator 워크플로우: docs/HARNESS.md

## 문제 보고 및 연락

유지보수자: MinHyeokYang

