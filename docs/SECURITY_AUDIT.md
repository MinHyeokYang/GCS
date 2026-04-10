# Security Audit — Team Todo API

**감사 일자**: 2026-04-07  
**감사 대상**: `app/` 전체 (routers, models, schemas, database)  
**감사 기준**: OWASP Top 10 (2021), CWE Top 25, REST API Security Best Practices

---

## 요약

| 등급 | 건수 |
|------|------|
| Critical | 2 |
| High | 4 |
| Medium | 4 |
| Low | 3 |
| Info | 2 |
| **합계** | **15** |

---

## Critical

### [SEC-01] 인증·인가 전면 미구현

- **위치**: 모든 엔드포인트
- **CWE**: CWE-306 (Missing Authentication for Critical Function)
- **OWASP**: A01:2021 – Broken Access Control

`POST /teams/{team_id}/todos`를 포함한 **전체 15개 엔드포인트**가 인증 없이 호출 가능하다.  
누구든 임의의 팀 데이터를 생성·수정·삭제할 수 있다.

> PRD §3 "Non-Goals"에 "인증/인가는 구현하지 않는다"고 명시되어 있으나,  
> 프로덕션 배포 전 반드시 해결해야 할 위험이다.

**권고**:
- JWT Bearer Token 또는 API Key 기반 인증 미들웨어 추가
- FastAPI `Depends`로 모든 write 엔드포인트에 인증 의존성 주입
- 팀 멤버십 검증을 서버 세션 기반으로 전환 (아래 SEC-02 참조)

---

### [SEC-02] `created_by` 클라이언트 공급 — IDOR

- **위치**: `app/schemas.py:125`, `app/routers/todos.py:56`
- **CWE**: CWE-639 (Authorization Bypass Through User-Controlled Key)
- **OWASP**: A01:2021 – Broken Access Control

```python
# schemas.py
created_by: int = Field(..., description="ID of the user creating this todo")
```

`created_by`는 요청 바디에서 클라이언트가 직접 전달한다.  
공격자가 `created_by: <타인의 user_id>`를 보내도 서버는 팀 멤버 여부만 확인하고 수락한다.  
→ 타인을 작성자로 위장한 Todo 생성이 가능하다.

```
POST /teams/1/todos
{"title": "악의적 todo", "created_by": 999, "status": "todo", "priority": "medium"}
# user 999가 실제로 팀 멤버이면 → 201 Created, creator = user 999
```

**권고**: 인증 구현 후 `created_by`를 JWT/세션에서 추출하고 요청 바디에서 제거.

---

## High

### [SEC-03] 크로스팀 데이터 격리 미흡

- **위치**: `app/routers/users.py:44`
- **CWE**: CWE-285 (Improper Authorization)
- **OWASP**: A01:2021 – Broken Access Control

`GET /users`는 **전체 사용자 목록**을 인증 없이 반환한다.  
이름, 이메일, 가입일이 모두 노출되므로 이메일 열거(enumeration) 공격에 직접 활용될 수 있다.

```http
GET /users HTTP/1.1
→ 200 OK
[{"id":1,"name":"Alice","email":"alice@corp.com","created_at":"..."}, ...]
```

**권고**:
- 인증 후 자신이 속한 팀의 멤버만 조회 가능하도록 범위 제한
- 또는 `/users` 엔드포인트에 관리자 권한 요구

---

### [SEC-04] 순차 정수 ID로 리소스 열거 가능

- **위치**: `app/models.py` — User, Team, Todo, Tag 모두 `autoincrement=True`
- **CWE**: CWE-330 (Use of Insufficiently Random Values)
- **OWASP**: A01:2021 – Broken Access Control

모든 리소스 ID가 1부터 순차 증가하므로 공격자가 `/teams/1/todos`, `/teams/2/todos` …를 순회하며 전체 데이터를 스캔할 수 있다.

**권고**: 공개 ID에는 UUID v4 또는 NanoID 사용.  
내부 PK는 정수를 유지하고 외부 노출 ID만 UUID로 분리하는 패턴 권장.

---

### [SEC-05] 속도 제한(Rate Limiting) 없음

- **위치**: `app/main.py`
- **CWE**: CWE-770 (Allocation of Resources Without Limits or Throttling)
- **OWASP**: A04:2021 – Insecure Design

인증 없는 상태에서 속도 제한도 없으므로 다음 공격에 무방비:
- 이메일 열거: `POST /users`에 임의 이메일 반복 전송으로 409/400 응답 차이로 존재 확인
- DoS: 무한 Todo 생성
- 무차별 대입: (인증 도입 후) 토큰/키 추측

**권고**:
- `slowapi` 또는 nginx upstream rate limit 적용
- IP별 요청 수를 분당 100회 등으로 제한

---

### [SEC-06] CORS 정책 미설정

- **위치**: `app/main.py`
- **CWE**: CWE-942 (Permissive Cross-domain Policy)
- **OWASP**: A05:2021 – Security Misconfiguration

`CORSMiddleware`가 추가되지 않아 브라우저 기반 클라이언트에서의 CORS 동작이 프레임워크 기본값에 의존한다.  
FastAPI 기본값은 CORS 헤더를 추가하지 않지만, 명시적으로 제어하지 않으면 역방향 프록시나 미들웨어 추가 시 의도치 않게 와일드카드(`*`)가 노출될 수 있다.

**권고**:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend.com"],  # 와일드카드 금지
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

---

## Medium

### [SEC-07] 데이터베이스 URL 하드코딩

- **위치**: `app/database.py:8`
- **CWE**: CWE-259 (Use of Hard-coded Password / Credentials)
- **OWASP**: A05:2021 – Security Misconfiguration

```python
SQLALCHEMY_DATABASE_URL = "sqlite:///./todo.db"
```

환경 변수가 아닌 소스 코드에 직접 작성되어 있다. SQLite 파일 경로가 유출되면 파일 시스템 접근 경로가 노출된다. PostgreSQL 등으로 전환 시 비밀번호가 코드에 포함될 위험이 있다.

**권고**:
```python
import os
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./todo.db")
```
`.env` 파일과 `python-dotenv` 또는 `pydantic-settings` 사용 권장.

---

### [SEC-08] HTTP 보안 헤더 미설정

- **위치**: `app/main.py`
- **CWE**: CWE-16 (Configuration)
- **OWASP**: A05:2021 – Security Misconfiguration

응답에 다음 헤더가 없다:

| 헤더 | 목적 |
|------|------|
| `X-Content-Type-Options: nosniff` | MIME sniffing 방지 |
| `X-Frame-Options: DENY` | Clickjacking 방지 |
| `Content-Security-Policy` | XSS 완화 |
| `Strict-Transport-Security` | HTTPS 강제 |

**권고**: `starlette.middleware` 또는 `secure` 패키지로 일괄 적용.

---

### [SEC-09] Swagger UI 인증 없이 공개

- **위치**: `app/main.py` — FastAPI 기본 설정
- **OWASP**: A05:2021 – Security Misconfiguration

`/docs`, `/redoc`, `/openapi.json`이 인증 없이 접근 가능하다.  
API 구조 전체가 외부에 노출되어 공격 표면 분석에 이용될 수 있다.

**권고**:
```python
# 프로덕션 환경에서는 비활성화
app = FastAPI(
    docs_url="/docs" if DEBUG else None,
    redoc_url="/redoc" if DEBUG else None,
)
```

---

### [SEC-10] `description` 필드 길이 제한 없음

- **위치**: `app/schemas.py:120`, `app/models.py:87`
- **CWE**: CWE-400 (Uncontrolled Resource Consumption)

```python
# schemas.py
description: str | None = Field(None, description="Optional detailed description")

# models.py
description: Mapped[str | None] = mapped_column(Text, nullable=True)
```

`description`에 상한이 없다. 수 MB 크기의 문자열을 전송해도 서버가 수락하며, SQLite Text 컬럼에 그대로 저장된다.

**권고**:
```python
description: str | None = Field(None, max_length=10_000, description="...")
```

---

## Low

### [SEC-11] 감사 로그(Audit Log) 없음

- **CWE**: CWE-223 (Omission of Security-relevant Information)

누가 어떤 Todo를 삭제했는지 추적할 방법이 없다. `deleted_by`, `deleted_at` 필드가 없고 애플리케이션 로그도 없다.

**권고**: 
- 삭제·수정 이벤트를 별도 `audit_logs` 테이블 또는 구조화 로그(`structlog`)로 기록
- FastAPI 미들웨어로 모든 write 요청 로깅

---

### [SEC-12] `todo.db` 파일 접근 권한 미제어

- **위치**: 프로젝트 루트 `todo.db`
- **CWE**: CWE-732 (Incorrect Permission Assignment for Critical Resource)

`todo.db`가 프로젝트 루트에 생성되며, 파일 시스템 권한이 명시적으로 설정되지 않는다. 공유 서버 환경에서 다른 사용자가 파일을 직접 읽을 수 있다.

**권고**: 
- 데이터 파일을 `/var/lib/app/` 등 별도 경로에 분리
- 파일 권한을 `chmod 600`으로 설정
- 장기적으로 PostgreSQL 등 서버 기반 DB로 전환

---

### [SEC-13] `todo.db`가 `.gitignore`에 포함되지 않을 경우 데이터 유출

- **CWE**: CWE-312 (Cleartext Storage of Sensitive Information)

SQLite 파일이 실수로 git에 커밋되면 전체 사용자 데이터(이름, 이메일)가 저장소 히스토리에 영구 보존된다.

**권고**: `.gitignore`에 `todo.db` 추가 및 pre-commit hook으로 `.db` 파일 커밋 차단.

---

## Info

### [SEC-14] IntegrityError 상세 메시지 노출 최소화

- **위치**: `app/routers/users.py:28`, `app/routers/tags.py:36`

현재 코드는 `IntegrityError`를 catch하여 사용자 친화적 메시지만 반환하고 있다 (양호).  
단, 예외 처리가 누락된 다른 write 경로에서 SQLAlchemy 내부 오류가 500 응답에 포함될 수 있으므로 글로벌 예외 핸들러 추가를 권장한다.

---

### [SEC-15] HTTPS 강제 없음

서버 자체에 TLS 설정이 없다. Uvicorn 직접 실행 시 HTTP로만 동작한다.  
내부 네트워크에서만 사용하는 경우 낮은 위험이지만, 공개망 배포 시 모든 데이터(이메일 등)가 평문 전송된다.

**권고**: nginx/Caddy 리버스 프록시에서 TLS 종료 설정.

---

## 위험 매트릭스

```
영향
 ^
 │  [SEC-01]  [SEC-02]
 │  [SEC-03]  [SEC-04]  [SEC-05]  [SEC-06]
 │           [SEC-07]  [SEC-08]  [SEC-09]  [SEC-10]
 │  [SEC-11] [SEC-12]  [SEC-13]
 │           [SEC-14]  [SEC-15]
 └────────────────────────────────────────────> 발생 가능성
   낮음        중간        높음
```

## 우선순위별 개선 로드맵

| 우선순위 | 항목 | 예상 공수 |
|----------|------|-----------|
| P0 — 즉시 | SEC-01: 인증 구현 | 2~3일 |
| P0 — 즉시 | SEC-02: `created_by` 서버 추출 | 인증 구현 후 0.5일 |
| P1 — 단기 | SEC-03: 사용자 목록 범위 제한 | 0.5일 |
| P1 — 단기 | SEC-05: Rate Limiting | 0.5일 |
| P1 — 단기 | SEC-06: CORS 설정 | 1시간 |
| P2 — 중기 | SEC-07: 환경변수 분리 | 1시간 |
| P2 — 중기 | SEC-08: 보안 헤더 | 1시간 |
| P2 — 중기 | SEC-09: Swagger 접근 제어 | 1시간 |
| P2 — 중기 | SEC-10: description 길이 제한 | 30분 |
| P3 — 장기 | SEC-04: UUID 전환 | 1일 |
| P3 — 장기 | SEC-11: 감사 로그 | 1일 |
| P3 — 장기 | SEC-12/13: DB 파일 보안 | 2시간 |
