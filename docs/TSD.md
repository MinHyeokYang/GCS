# TSD - Team Todo 백엔드 기술 명세

업데이트: 2026-04-10

## 1. 기술 스택
- Python 3.11+
- FastAPI
- SQLAlchemy 2.x
- Pydantic v2
- Alembic
- SQLite
- Uvicorn

## 2. 로컬 개발 도구
- 환경/실행: `uv`
- 명령 실행: `uv run ...`
- 단일 패키지 실행: `uvx ...`

## 3. 프로젝트 구조
```text
app/
  main.py
  database.py
  models.py
  schemas.py
  routers/
    users.py
    teams.py
    todos.py
    tags.py
    comments.py
cli/
  main.py
  adapter.py
tests/
alembic/
docs/
```

## 4. 데이터 접근 규칙
- DB URL: `TODO_DATABASE_URL` (기본값 `sqlite:///./todo.db`)
- `get_db()` 의존성으로 세션 주입/종료
- SQLite 연결 시 `PRAGMA foreign_keys=ON` 적용

## 5. API 설계 원칙
- REST 리소스 구조
- 팀 스코프 하위 리소스(Todo/Tag/Comment) 사용
- 요청/응답 스키마를 Pydantic으로 엄격하게 검증
- Swagger/ReDoc/OpenAPI 자동 제공

## 6. 상태코드 규칙
- `201`: 생성 성공
- `200`: 조회/수정 성공
- `204`: 삭제 성공
- `400`: 도메인 제약 위반
- `404`: 리소스 없음
- `409`: 충돌(삭제 제한 등)
- `422`: 입력 검증 실패

## 7. 마이그레이션
```bash
uv run alembic upgrade head
uv run alembic downgrade -1
```

## 8. 실행 절차
```bash
uv venv
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

접속 URL:
- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/redoc`
- `http://127.0.0.1:8000/openapi.json`

## 9. 테스트 전략
- API 단위/통합: `pytest` + FastAPI `TestClient`
- CLI E2E: uvicorn subprocess + CLI subprocess
- 부하 테스트: `httpx` 동시성 시나리오
