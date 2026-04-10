# PRD — Team Todo App Backend

**언어:** 한국어 | **대상:** 개발자 · 기획자 | **마지막 수정:** 2026-04-10



## 1. Overview

팀 멤버가 함께 사용하는 Todo 관리 백엔드 서비스.
팀 단위로 Todo를 생성·관리하고, 담당자 할당 및 상태 추적을 지원한다.

## 2. Goals

- 팀 단위로 Todo 항목을 공유하고 관리할 수 있다.
- Todo에 담당자, 마감일, 우선순위, 태그, 상태를 설정할 수 있다.
- REST API로 모든 기능에 접근할 수 있다.
- FastAPI 내장 Swagger(`/docs`)로 API 문서를 제공한다.

## 3. Non-Goals

- 인증/인가 (Auth) 는 구현하지 않는다.
- 실시간 동기화 (WebSocket / SSE) 는 구현하지 않는다.
- 프로덕션 배포는 현재 범위에 포함되지 않는다.

## 4. User Stories

### 팀 관리
- 사용자는 팀을 만들 수 있다.
- 사용자는 팀에 멤버를 추가하거나 제거할 수 있다.
- 사용자는 자신이 속한 팀 목록을 조회할 수 있다.

### Todo 관리
- 팀 멤버는 팀 내에 Todo를 생성할 수 있다.
- 팀 멤버는 Todo 목록을 조회할 수 있다. (status, priority, assignee, tag 필터 지원)
- 팀 멤버는 Todo의 내용과 상태를 수정할 수 있다.
- 팀 멤버는 Todo를 삭제할 수 있다.

### 태그 관리
- 팀 멤버는 팀 내에서 사용할 태그를 만들 수 있다.
- 팀 멤버는 Todo에 태그를 부착하거나 제거할 수 있다.

## 5. Functional Requirements

| ID | 요구사항 |
|----|---------|
| F-01 | 유저 생성 및 목록 조회 |
| F-02 | 팀 생성, 조회, 멤버 추가/제거 |
| F-03 | Todo CRUD (팀 범위) |
| F-04 | Todo 필드: title, description, status, priority, due_date, assignee |
| F-05 | Todo 목록 필터링: status, priority, assignee_id, tag_id |
| F-06 | 태그 생성, 목록 조회, Todo에 부착/제거 |
| F-07 | `/docs` 에서 Swagger UI 제공 |

## 6. Non-Functional Requirements

| ID | 요구사항 |
|----|---------|
| NF-01 | 로컬 환경에서 실행 가능 |
| NF-02 | SQLite 파일 기반 영속성 |
| NF-03 | 응답 형식은 JSON |
| NF-04 | HTTP 상태 코드를 의미에 맞게 사용 (200, 201, 404, 422 등) |

## 7. API Summary

| Method | Path | 설명 |
|--------|------|------|
| POST | /users | 유저 생성 |
| GET | /users | 유저 목록 |
| POST | /teams | 팀 생성 |
| GET | /teams/{team_id} | 팀 정보 조회 |
| POST | /teams/{team_id}/members | 팀 멤버 추가 |
| DELETE | /teams/{team_id}/members/{user_id} | 팀 멤버 제거 |
| POST | /teams/{team_id}/todos | Todo 생성 |
| GET | /teams/{team_id}/todos | Todo 목록 (필터 지원) |
| GET | /teams/{team_id}/todos/{todo_id} | Todo 단건 조회 |
| PATCH | /teams/{team_id}/todos/{todo_id} | Todo 수정 |
| DELETE | /teams/{team_id}/todos/{todo_id} | Todo 삭제 |
| POST | /teams/{team_id}/tags | 태그 생성 |
| GET | /teams/{team_id}/tags | 태그 목록 |
| POST | /teams/{team_id}/todos/{todo_id}/tags/{tag_id} | Todo에 태그 부착 |
| DELETE | /teams/{team_id}/todos/{todo_id}/tags/{tag_id} | Todo에서 태그 제거 |
