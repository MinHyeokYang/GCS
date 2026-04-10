# Performance Audit — Team Todo API

**감사 일자**: 2026-04-07  
**감사 대상**: `app/` 전체 + 스트레스 테스트 (`tests/test_stress_concurrent.py`)  
**테스트 환경**: Python 3.11.9 / FastAPI / SQLite / httpx.ASGITransport / NullPool

---

## 요약

| 등급 | 건수 |
|------|------|
| Critical | 1 |
| High | 3 |
| Medium | 3 |
| Low | 2 |
| **합계** | **9** |

---

## 스트레스 테스트 결과

### 테스트 설계

- **방법**: `httpx.AsyncClient` + `httpx.ASGITransport` — 실제 서버 없이 ASGI 레이어에서 직접 호출
- **DB 풀**: `NullPool` (요청마다 새 커넥션) — 프로덕션 고부하 상황 모사
- **데이터**: 사용자 5명, 팀 1개, Todo 20개 사전 시드

### 시나리오별 결과

#### 시나리오 1: 동시 읽기 (concurrency=20, total=100)

```
Total     : 100
OK        : 100
Error rate: 0.0%
Latency (ms)
  min  :   34.8
  mean :  101.6
  p50  :   98.7
  p95  :  143.8
  p99  :  164.4
  max  :  164.4
```

- **판정**: 정상. 읽기 요청은 SQLite 공유 읽기 잠금으로 충분히 처리됨.
- **주목**: concurrency=20에서도 p95 144ms — SQLite read 성능은 양호.

---

#### 시나리오 2: 동시 쓰기 (concurrency=10, total=50)

```
Total     : 50
OK        : 50
Error rate: 0.0%
Latency (ms)
  min  :   23.9
  mean :  220.5
  p50  :  137.5
  p95  : 1001.4
  p99  : 1184.1
  max  : 1184.1
```

- **판정**: 경고. p95가 **1초**를 초과.
- **원인**: SQLite는 파일 단위 write lock. 동시 writer 10명이 직렬 대기 → latency가 writer 수에 비례해 선형 증가.
- **참고**: 에러 없이 모두 완료되었으나 응답 시간이 허용 한계에 근접.

---

#### 시나리오 3: 혼합 읽기/쓰기 (concurrency=15, total=100)

```
Total     : 100
OK        : 100
Error rate: 0.0%
Latency (ms)
  min  :    9.8
  mean :  131.9
  p50  :   96.4
  p95  :  328.7
  p99  :  977.6
  max  :  977.6
```

- **판정**: 경고. p99 978ms — write 경합 시 꼬리 지연(tail latency)이 높음.
- **원인**: 읽기 요청은 빠르지만 쓰기 요청이 잠금을 획득하는 동안 뒤따르는 요청들이 줄을 선다.

---

#### 시나리오 4: 커넥션 풀 버스트 (concurrency=200, total=200)

```
Total     : 200
OK        : 200
Error rate: 0.0%
Latency (ms)
  min  :  1847.0
  mean :  2088.7
  p50  :  2086.1
  p95  :  2341.2
  p99  :  2396.8
  max  :  2408.9
```

- **판정**: 위험. 200개 동시 요청 시 **p50 2.1초, p99 2.4초**.
- **원인**: FastAPI의 동기 핸들러는 `anyio` worker thread pool에서 실행됨. 기본 thread pool 크기 초과 시 요청이 큐에 대기.
- **풀 에러**: 없음 — NullPool이므로 커넥션 고갈은 없지만 thread 포화로 latency가 급등.

---

#### 시나리오 5: 동일 행 쓰기 경합 (concurrency=10, total=30)

```
Total     : 30
OK        : 30
Error rate: 0.0%
Latency (ms)
  min  :   62.1
  mean :  162.7
  p50  :  154.6
  p95  :  270.4
  p99  :  279.1
  max  :  279.1
```

- **판정**: 정상. 동일 행에 대한 PATCH 경합도 SQLite 트랜잭션이 직렬화하므로 에러 없이 처리됨.

---

### 중대 발견: StaticPool 동시 쓰기 버그

테스트 DB를 `StaticPool`(단위 테스트 conftest.py 설정)로 변경하면 동시 쓰기 시 **즉시 에러** 발생:

```
sqlite3.DatabaseError: no more rows available
sqlalchemy.exc.InvalidRequestError: Could not refresh instance '<Todo at 0x...>'
```

**원인**: `StaticPool`은 모든 세션이 단일 커넥션을 공유함. FastAPI가 `anyio.to_thread.run_sync`로 핸들러를 worker thread에서 실행하면, 여러 스레드가 같은 커넥션의 커서를 동시에 사용해 상태 충돌 발생.

**영향**: 단위 테스트에서 `StaticPool` + 동시 write 시 테스트가 잘못된 에러를 리포트할 수 있음. 프로덕션(`QueuePool`)에서는 재현되지 않지만 테스트 신뢰도에 영향.

**해결**: 동시성 테스트에는 `NullPool` 또는 실제 파일 기반 SQLite + `QueuePool` 사용.

---

## 코드 수준 성능 이슈

### [PERF-01] 무한 페이지네이션 — 목록 엔드포인트 전체 반환

- **위치**: `app/routers/users.py:44`, `app/routers/todos.py:93`, `app/routers/tags.py:53`
- **등급**: Critical

```python
# users.py
def list_users(db: Session = Depends(get_db)) -> list[User]:
    return db.query(User).all()  # LIMIT 없음

# todos.py
return q.all()  # LIMIT 없음
```

레코드 수가 증가해도 전체를 메모리에 올려 직렬화한다.  
10만 건의 Todo가 있는 팀에서 `GET /teams/1/todos`를 호출하면 서버 OOM 가능.

**권고**:
```python
# Query parameter 추가
def list_todos(
    ...
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[Todo]:
    return q.offset(offset).limit(limit).all()
```

---

### [PERF-02] N+1 쿼리 위험 — `_get_team_or_404` 중복 호출

- **위치**: `app/routers/todos.py:56–76` (`create_todo`)
- **등급**: High

```python
def create_todo(team_id: int, body: TodoCreate, db: Session = Depends(get_db)) -> Todo:
    _get_team_or_404(team_id, db)          # 쿼리 1: SELECT team
    _assert_team_member(...)               # 쿼리 2: SELECT member
    ...
    db.commit()
    db.refresh(todo)                       # 쿼리 3: SELECT todo
    return _get_todo_or_404(todo.id, ...)  # 쿼리 4: SELECT todo + selectinload (중복!)
```

`create_todo`는 `db.refresh(todo)` 후 다시 `_get_todo_or_404`를 호출해 **같은 Todo를 두 번** 조회한다. `db.refresh`로 이미 최신 상태를 로드했으므로 마지막 `_get_todo_or_404`는 불필요한 round-trip이다.

동일 패턴이 `update_todo`에도 존재 (`todos.py:152`).

**권고**: `db.refresh` 후 `selectinload`만 별도로 실행하거나, `refresh` 시 eager load 옵션 포함.

---

### [PERF-03] `status`, `priority` 컬럼에 인덱스 없음

- **위치**: `app/models.py:87–88`
- **등급**: High

```python
status: Mapped[str] = mapped_column(VARCHAR(20), nullable=False, default="todo")
priority: Mapped[str] = mapped_column(VARCHAR(10), nullable=False, default="medium")
```

`list_todos`에서 두 컬럼이 필터로 자주 사용되지만 인덱스가 없다:

```python
# todos.py:102–105
if todo_status is not None:
    q = q.filter(Todo.status == todo_status.value)   # full scan
if priority is not None:
    q = q.filter(Todo.priority == priority.value)    # full scan
```

Todo가 수만 건 이상일 때 쿼리마다 full table scan 발생.

**권고**: Alembic 마이그레이션으로 인덱스 추가.
```python
# models.py
status: Mapped[str] = mapped_column(
    VARCHAR(20), nullable=False, default="todo", index=True
)
priority: Mapped[str] = mapped_column(
    VARCHAR(10), nullable=False, default="medium", index=True
)
```

---

### [PERF-04] `TodoTag` JOIN에 복합 인덱스 없음

- **위치**: `app/models.py:146–151`, `app/routers/todos.py:109`
- **등급**: High

```python
# todos.py
if tag_id is not None:
    q = q.join(TodoTag).filter(TodoTag.tag_id == tag_id)
```

`TodoTag`는 `(todo_id, tag_id)` 복합 PK를 가지지만, `tag_id` 단독 조회 시 인덱스 탐색이 PK 순서 기준이라 `tag_id` 기준 필터는 full scan에 가깝다.

**권고**: `tag_id`에 단독 인덱스 추가.
```python
tag_id: Mapped[int] = mapped_column(
    Integer, ForeignKey("tags.id", ondelete="CASCADE"),
    primary_key=True, index=True
)
```

---

### [PERF-05] 프로덕션 커넥션 풀 설정 미명시

- **위치**: `app/database.py:10–13`
- **등급**: Medium

```python
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    # pool_size, max_overflow, pool_timeout 미설정 → 기본값 의존
)
```

SQLAlchemy 기본값:
- `pool_size=5` (동시 커넥션 5개 유지)
- `max_overflow=10` (최대 15개까지 확장)
- `pool_timeout=30s` (커넥션 대기 타임아웃)

SQLite는 단일 파일 기반으로 writer 직렬화가 필요하므로 `QueuePool`에서 여러 writer가 연결을 보유한 채 대기하면 데드락 유사 상황 발생 가능. 스트레스 테스트(시나리오 4)에서 p50 2.1초가 이 구조에서 기인한다.

**권고** (단기):
```python
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    pool_size=5,
    max_overflow=0,      # overflow 방지 — writer 직렬화 명시
    pool_timeout=10,     # 10초 내 커넥션 미획득 시 즉시 503
    pool_pre_ping=True,  # stale 커넥션 자동 재연결
)
```

**권고** (장기): 동시 쓰기 빈도가 높아지면 PostgreSQL으로 전환.

---

### [PERF-06] 동기 핸들러 + 대규모 동시 요청 시 Thread Pool 포화

- **위치**: `app/routers/*.py` — 모든 핸들러가 `def`(동기)
- **등급**: Medium

FastAPI는 동기 핸들러를 `anyio.to_thread.run_sync`로 worker thread에서 실행한다.  
기본 thread pool 크기는 약 40~80개(시스템 설정에 따라 다름). 동시 요청 200개(시나리오 4)에서 p50이 2.1초로 급등한 것은 thread pool 포화가 주 원인이다.

```
동시 요청 200개 → thread pool(~40) 포화 → 160개 요청 대기 큐 → latency 급등
```

**권고**:
- 핵심 read 엔드포인트는 `async def`로 전환 + `AsyncSession` 사용
- 또는 `uvicorn --workers N`으로 프로세스 수 늘리기 (multiprocessing)

---

### [PERF-07] `selectinload` 사용은 적절하나 불필요한 시나리오에서도 항상 실행

- **위치**: `app/routers/todos.py:96–100`, `app/routers/todos.py:23–28`
- **등급**: Medium

```python
q = (
    db.query(Todo)
    .options(selectinload(Todo.todo_tags).selectinload(TodoTag.tag))
    ...
)
```

`selectinload`는 N+1 방지를 위한 올바른 선택이지만, 태그가 없는 Todo를 조회할 때도 `SELECT * FROM todo_tags WHERE todo_id IN (...)` 쿼리가 항상 발행된다. 태그를 거의 사용하지 않는 팀에서는 불필요한 쿼리 오버헤드가 된다.

**권고**: 클라이언트가 `include_tags=false`를 요청할 수 있도록 선택적 로드 파라미터 제공 (선택 사항).

---

### [PERF-08] SQLite WAL 모드 미설정

- **위치**: `app/database.py`
- **등급**: Low

SQLite 기본 저널 모드(`DELETE`)는 write 시 reader를 포함한 모든 연결을 블로킹한다. WAL(Write-Ahead Logging) 모드를 활성화하면 writer가 reader를 블로킹하지 않아 혼합 워크로드(시나리오 3)에서 p99를 유의미하게 낮출 수 있다.

**권고**:
```python
from sqlalchemy import event

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, _):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")  # 성능/안전성 균형
    cursor.close()
```

---

### [PERF-09] `due_date` 컬럼에 인덱스 없음 (미래 기능 대비)

- **위치**: `app/models.py:89`
- **등급**: Low

마감일 기반 조회(`due_date <= today`)가 추가될 경우 인덱스 없이 full scan.  
현재는 사용되지 않으므로 낮은 우선순위이나 스키마 설계 단계에서 추가 권장.

---

## 성능 개선 우선순위 로드맵

| 우선순위 | 항목 | 예상 효과 | 공수 |
|----------|------|-----------|------|
| P0 | PERF-01: 페이지네이션 | OOM 방지, 응답 크기 제어 | 1일 |
| P0 | PERF-03: status/priority 인덱스 | 필터 쿼리 수십 배 개선 | 1시간 |
| P1 | PERF-02: 중복 쿼리 제거 | 요청당 쿼리 수 25% 감소 | 2시간 |
| P1 | PERF-05: 풀 설정 명시 | 타임아웃 제어, 안정성 향상 | 30분 |
| P1 | PERF-08: WAL 모드 활성화 | 혼합 워크로드 p99 개선 | 30분 |
| P2 | PERF-04: TodoTag tag_id 인덱스 | 태그 필터 쿼리 개선 | 30분 |
| P2 | PERF-06: async 핸들러 전환 | 고동시성 처리량 개선 | 2~3일 |
| P3 | PERF-07: 선택적 태그 로드 | 태그 없는 팀 성능 최적화 | 1일 |
| P3 | PERF-09: due_date 인덱스 | 미래 기능 대비 | 30분 |

---

## 개선 전후 예상 지표 (SQLite 유지 기준)

| 시나리오 | 현재 p95 | WAL + 인덱스 후 예상 p95 | async 전환 후 예상 p95 |
|----------|----------|--------------------------|------------------------|
| 동시 읽기(20) | 144ms | ~80ms | ~50ms |
| 동시 쓰기(10) | 1001ms | ~600ms | ~400ms |
| 혼합 R/W(15) | 329ms | ~150ms | ~100ms |
| 풀 버스트(200) | 2341ms | ~1500ms | ~500ms |

> 예상 수치는 SQLite 파일 기반 특성(단일 writer)을 고려한 보수적 추정.  
> PostgreSQL 전환 시 동시 쓰기 p95는 수십 ms 수준으로 개선 가능.
