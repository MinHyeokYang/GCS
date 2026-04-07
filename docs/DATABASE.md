# DATABASE.md — Database Design

## 1. Overview

- DBMS: SQLite
- ORM: SQLAlchemy 2.0
- 파일 경로: `./todo.db` (프로젝트 루트)

---

## 2. ERD (Entity Relationship)

```
User ──< TeamMember >── Team
                          │
                        Todo ──< TodoTag >── Tag
                          │
                        User (assignee)
```

---

## 3. Tables

### 3.1 `users`

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | INTEGER | PK, autoincrement | 유저 ID |
| name | VARCHAR(100) | NOT NULL | 이름 |
| email | VARCHAR(255) | NOT NULL, UNIQUE | 이메일 |
| created_at | DATETIME | NOT NULL, default=now | 생성일시 |

---

### 3.2 `teams`

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | INTEGER | PK, autoincrement | 팀 ID |
| name | VARCHAR(100) | NOT NULL | 팀 이름 |
| created_at | DATETIME | NOT NULL, default=now | 생성일시 |

---

### 3.3 `team_members` (다대다 연결 테이블)

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| team_id | INTEGER | FK → teams.id, PK | 팀 ID |
| user_id | INTEGER | FK → users.id, PK | 유저 ID |
| joined_at | DATETIME | NOT NULL, default=now | 가입일시 |

- PK: (team_id, user_id) 복합키

---

### 3.4 `todos`

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | INTEGER | PK, autoincrement | Todo ID |
| title | VARCHAR(255) | NOT NULL | 제목 |
| description | TEXT | nullable | 상세 내용 |
| status | VARCHAR(20) | NOT NULL, default='todo' | todo / in_progress / done |
| priority | VARCHAR(10) | NOT NULL, default='medium' | low / medium / high |
| due_date | DATE | nullable | 마감일 |
| team_id | INTEGER | FK → teams.id, NOT NULL | 소속 팀 |
| assignee_id | INTEGER | FK → users.id, nullable | 담당자 |
| created_by | INTEGER | FK → users.id, NOT NULL | 생성자 |
| created_at | DATETIME | NOT NULL, default=now | 생성일시 |
| updated_at | DATETIME | NOT NULL, default=now, onupdate=now | 수정일시 |

---

### 3.5 `tags`

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | INTEGER | PK, autoincrement | 태그 ID |
| name | VARCHAR(50) | NOT NULL | 태그 이름 |
| team_id | INTEGER | FK → teams.id, NOT NULL | 소속 팀 |

- UNIQUE: (name, team_id) — 같은 팀 내 태그 이름 중복 불가

---

### 3.6 `todo_tags` (다대다 연결 테이블)

| 컬럼 | 타입 | 제약 | 설명 |
|------|------|------|------|
| todo_id | INTEGER | FK → todos.id, PK | Todo ID |
| tag_id | INTEGER | FK → tags.id, PK | 태그 ID |

- PK: (todo_id, tag_id) 복합키

---

## 4. 관계 정리

| 관계 | 설명 |
|------|------|
| User — Team | 다대다 (team_members 경유) |
| Team — Todo | 일대다 |
| User — Todo (assignee) | 일대다 (nullable) |
| User — Todo (created_by) | 일대다 |
| Todo — Tag | 다대다 (todo_tags 경유) |
| Team — Tag | 일대다 (태그는 팀 소속) |

---

## 5. 인덱스 권고

| 테이블 | 컬럼 | 이유 |
|--------|------|------|
| todos | team_id | 팀별 Todo 조회 빈번 |
| todos | assignee_id | 담당자 필터링 |
| todos | status | 상태 필터링 |
| todos | priority | 우선순위 필터링 |
| todo_tags | tag_id | 태그별 Todo 조회 |
