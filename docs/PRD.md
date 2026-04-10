# PRD - Team Todo 백엔드

업데이트: 2026-04-10

## 1. 제품 개요
팀 멤버가 함께 사용하는 Todo 백엔드 서비스다.  
팀 단위로 할 일을 생성/조회/수정/삭제하고, 태그/댓글로 협업 맥락을 남긴다.

## 2. 목표
- 팀 단위 Todo 협업 지원
- 담당자, 마감일, 우선순위, 상태 관리
- 태그/댓글을 통한 분류 및 커뮤니케이션
- FastAPI Swagger 기반 API 문서 제공

## 3. 범위 제외
- 인증/인가
- 실시간 기능(WebSocket/SSE)
- 운영 인프라 자동화

## 4. 사용자 시나리오
- 팀 멤버는 Todo를 만들고 상태를 변경한다.
- 팀 멤버는 다른 멤버를 담당자로 지정한다.
- 팀 멤버는 태그를 붙여 Todo를 분류한다.
- 팀 멤버는 댓글로 작업 맥락을 남긴다.

## 5. 기능 요구사항
- FR-01 사용자: 생성/목록/상세/수정/삭제
- FR-02 팀: 생성/목록/상세/수정
- FR-03 팀 멤버: 추가/제거
- FR-04 Todo: 생성/목록/상세/수정/삭제
- FR-05 Todo 필터: `status`, `priority`, `assignee_id`, `tag_id`
- FR-06 태그: 생성/목록/상세/수정 + Todo 부착/해제
- FR-07 댓글: 생성/목록/상세/수정/삭제
- FR-08 API 문서: `/docs`, `/redoc`, `/openapi.json`

## 6. 비기능 요구사항
- Python 3.11+ 로컬 실행 가능
- SQLite 영속 저장
- JSON 응답 표준화
- HTTP 상태코드 일관성 (`200`, `201`, `204`, `400`, `404`, `409`, `422`)

## 7. API 요약
### Users
- `POST /users`
- `GET /users`
- `GET /users/{user_id}`
- `PATCH /users/{user_id}`
- `DELETE /users/{user_id}`

### Teams
- `POST /teams`
- `GET /teams`
- `GET /teams/{team_id}`
- `PATCH /teams/{team_id}`
- `POST /teams/{team_id}/members`
- `DELETE /teams/{team_id}/members/{user_id}`

### Todos
- `POST /teams/{team_id}/todos`
- `GET /teams/{team_id}/todos`
- `GET /teams/{team_id}/todos/{todo_id}`
- `PATCH /teams/{team_id}/todos/{todo_id}`
- `DELETE /teams/{team_id}/todos/{todo_id}`

### Tags
- `POST /teams/{team_id}/tags`
- `GET /teams/{team_id}/tags`
- `GET /teams/{team_id}/tags/{tag_id}`
- `PATCH /teams/{team_id}/tags/{tag_id}`
- `POST /teams/{team_id}/todos/{todo_id}/tags/{tag_id}`
- `DELETE /teams/{team_id}/todos/{todo_id}/tags/{tag_id}`

### Comments
- `POST /teams/{team_id}/todos/{todo_id}/comments`
- `GET /teams/{team_id}/todos/{todo_id}/comments`
- `GET /teams/{team_id}/todos/{todo_id}/comments/{comment_id}`
- `PATCH /teams/{team_id}/todos/{todo_id}/comments/{comment_id}`
- `DELETE /teams/{team_id}/todos/{todo_id}/comments/{comment_id}`
