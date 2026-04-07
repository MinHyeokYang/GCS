# TSD — Technical Specification Document

## 1. Tech Stack

| 항목 | 선택 | 버전 |
|------|------|------|
| Language | Python | 3.11+ |
| Framework | FastAPI | 0.111+ |
| ORM | SQLAlchemy | 2.0+ |
| DB | SQLite | - |
| Migration | Alembic | 1.13+ |
| Validation | Pydantic v2 | 2.0+ |
| Server | Uvicorn | 0.29+ |

## 2. Project Structure

```
app/
  main.py           # FastAPI 앱 진입점, 라우터 등록, Swagger 설정
  database.py       # SQLite 연결, 세션 팩토리, Base
  models.py         # SQLAlchemy ORM 모델
  schemas.py        # Pydantic request/response 스키마
  routers/
    users.py        # /users
    teams.py        # /teams
    todos.py        # /teams/{team_id}/todos
    tags.py         # /teams/{team_id}/tags
alembic/
  env.py
  versions/         # 마이그레이션 파일
alembic.ini
docs/
  PRD.md
  TSD.md
  DATABASE.md
requirements.txt
```

## 3. Application Entry Point (`main.py`)

```python
app = FastAPI(
    title="Team Todo API",
    version="1.0.0",
    description="팀 단위 Todo 관리 백엔드"
)
```

- 모든 라우터를 `include_router`로 등록
- 테이블 생성은 `Base.metadata.create_all()` 대신 Alembic 마이그레이션으로 관리
- `/docs` — Swagger UI
- `/redoc` — ReDoc

## 4. Database (`database.py`)

```python
SQLALCHEMY_DATABASE_URL = "sqlite:///./todo.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
```

- `check_same_thread=False` : FastAPI의 멀티스레드 환경 대응
- DB 파일: 프로젝트 루트의 `todo.db`

### Dependency

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

## 5. Swagger 문서 품질 기준

각 엔드포인트는 아래를 반드시 포함한다.

| 항목 | 방법 |
|------|------|
| 그룹핑 | `router = APIRouter(tags=["Todos"])` |
| 요약 | `@router.get(..., summary="Todo 목록 조회")` |
| 설명 | docstring 또는 `description=` 파라미터 |
| 응답 모델 | `response_model=TodoResponse` |
| 상태 코드 | `status_code=status.HTTP_201_CREATED` |

Pydantic 스키마 필드에는 `Field(description=...)` 을 추가해 Swagger에 필드 설명이 표시되도록 한다.

## 6. Error Handling

| 상황 | HTTP 상태 코드 |
|------|--------------|
| 리소스 없음 | 404 Not Found |
| 유효성 오류 | 422 Unprocessable Entity (FastAPI 자동 처리) |
| 생성 성공 | 201 Created |
| 조회/수정/삭제 성공 | 200 OK |
| 내용 없는 삭제 성공 | 204 No Content |

## 7. Todo Status & Priority Enum

```python
class TodoStatus(str, Enum):
    todo = "todo"
    in_progress = "in_progress"
    done = "done"

class Priority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
```

## 8. Dependencies

```
fastapi
uvicorn[standard]
sqlalchemy
alembic
pydantic[email]
```

## 9. Alembic 마이그레이션

```bash
# 초기 설정 (최초 1회)
alembic init alembic

# 마이그레이션 파일 생성
alembic revision --autogenerate -m "init"

# 마이그레이션 적용
alembic upgrade head

# 이전 버전으로 롤백
alembic downgrade -1
```

`alembic/env.py` 에서 `target_metadata = Base.metadata` 로 설정해야 autogenerate가 동작한다.

## 10. 실행 방법

```bash
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

접속: http://localhost:8000/docs
