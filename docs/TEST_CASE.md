# TEST_CASE — Team Todo API

> PRD의 Functional Requirements(F-01 ~ F-07) 기반으로 작성.
> 각 케이스는 `endpoint / request / expected response` 를 포함하며 체크리스트 형태로 정리.

---

## 1. 유저 (Users)

### TC-U-01 유저 생성 — 성공
- [ ] **Endpoint** `POST /users`
- [ ] **Request**
  ```json
  { "name": "Alice" }
  ```
- [ ] **Expected Response** `201 Created`
  ```json
  { "id": 1, "name": "Alice" }
  ```

### TC-U-02 유저 생성 — 실패 (name 누락)
- [ ] **Endpoint** `POST /users`
- [ ] **Request**
  ```json
  {}
  ```
- [ ] **Expected Response** `422 Unprocessable Entity`
  ```json
  { "detail": [{ "loc": ["body", "name"], "msg": "field required" }] }
  ```

### TC-U-03 유저 목록 조회 — 성공
- [ ] **Endpoint** `GET /users`
- [ ] **Request** (body 없음)
- [ ] **Expected Response** `200 OK`
  ```json
  [
    { "id": 1, "name": "Alice" },
    { "id": 2, "name": "Bob" }
  ]
  ```

### TC-U-04 유저 목록 조회 — 빈 목록
- [ ] **Endpoint** `GET /users`
- [ ] **Request** (body 없음, 유저 없는 상태)
- [ ] **Expected Response** `200 OK`
  ```json
  []
  ```

---

## 2. 팀 (Teams)

### TC-T-01 팀 생성 — 성공
- [ ] **Endpoint** `POST /teams`
- [ ] **Request**
  ```json
  { "name": "Dev Team" }
  ```
- [ ] **Expected Response** `201 Created`
  ```json
  { "id": 1, "name": "Dev Team", "members": [] }
  ```

### TC-T-02 팀 생성 — 실패 (name 누락)
- [ ] **Endpoint** `POST /teams`
- [ ] **Request**
  ```json
  {}
  ```
- [ ] **Expected Response** `422 Unprocessable Entity`

### TC-T-03 팀 정보 조회 — 성공
- [ ] **Endpoint** `GET /teams/1`
- [ ] **Request** (body 없음)
- [ ] **Expected Response** `200 OK`
  ```json
  { "id": 1, "name": "Dev Team", "members": [{ "id": 1, "name": "Alice" }] }
  ```

### TC-T-04 팀 정보 조회 — 실패 (존재하지 않는 팀)
- [ ] **Endpoint** `GET /teams/999`
- [ ] **Request** (body 없음)
- [ ] **Expected Response** `404 Not Found`
  ```json
  { "detail": "Team not found" }
  ```

---

## 3. 팀 멤버 (Team Members)

### TC-M-01 팀 멤버 추가 — 성공
- [ ] **Endpoint** `POST /teams/1/members`
- [ ] **Request**
  ```json
  { "user_id": 1 }
  ```
- [ ] **Expected Response** `201 Created`
  ```json
  { "id": 1, "name": "Dev Team", "members": [{ "id": 1, "name": "Alice" }] }
  ```

### TC-M-02 팀 멤버 추가 — 실패 (존재하지 않는 유저)
- [ ] **Endpoint** `POST /teams/1/members`
- [ ] **Request**
  ```json
  { "user_id": 999 }
  ```
- [ ] **Expected Response** `404 Not Found`
  ```json
  { "detail": "User not found" }
  ```

### TC-M-03 팀 멤버 추가 — 실패 (존재하지 않는 팀)
- [ ] **Endpoint** `POST /teams/999/members`
- [ ] **Request**
  ```json
  { "user_id": 1 }
  ```
- [ ] **Expected Response** `404 Not Found`
  ```json
  { "detail": "Team not found" }
  ```

### TC-M-04 팀 멤버 제거 — 성공
- [ ] **Endpoint** `DELETE /teams/1/members/1`
- [ ] **Request** (body 없음)
- [ ] **Expected Response** `204 No Content`

### TC-M-05 팀 멤버 제거 — 실패 (멤버가 아닌 유저)
- [ ] **Endpoint** `DELETE /teams/1/members/999`
- [ ] **Request** (body 없음)
- [ ] **Expected Response** `404 Not Found`
  ```json
  { "detail": "Member not found" }
  ```

---

## 4. Todo CRUD

### TC-TODO-01 Todo 생성 — 성공 (필수 필드만)
- [ ] **Endpoint** `POST /teams/1/todos`
- [ ] **Request**
  ```json
  { "title": "API 설계 완료" }
  ```
- [ ] **Expected Response** `201 Created`
  ```json
  {
    "id": 1,
    "title": "API 설계 완료",
    "description": null,
    "status": "todo",
    "priority": "medium",
    "due_date": null,
    "assignee": null,
    "tags": []
  }
  ```

### TC-TODO-02 Todo 생성 — 성공 (모든 필드)
- [ ] **Endpoint** `POST /teams/1/todos`
- [ ] **Request**
  ```json
  {
    "title": "DB 스키마 작성",
    "description": "ERD 기반으로 SQLAlchemy 모델 작성",
    "status": "in_progress",
    "priority": "high",
    "due_date": "2026-04-30",
    "assignee_id": 1
  }
  ```
- [ ] **Expected Response** `201 Created`
  ```json
  {
    "id": 2,
    "title": "DB 스키마 작성",
    "description": "ERD 기반으로 SQLAlchemy 모델 작성",
    "status": "in_progress",
    "priority": "high",
    "due_date": "2026-04-30",
    "assignee": { "id": 1, "name": "Alice" },
    "tags": []
  }
  ```

### TC-TODO-03 Todo 생성 — 실패 (title 누락)
- [ ] **Endpoint** `POST /teams/1/todos`
- [ ] **Request**
  ```json
  { "priority": "high" }
  ```
- [ ] **Expected Response** `422 Unprocessable Entity`

### TC-TODO-04 Todo 생성 — 실패 (유효하지 않은 status 값)
- [ ] **Endpoint** `POST /teams/1/todos`
- [ ] **Request**
  ```json
  { "title": "테스트", "status": "invalid_status" }
  ```
- [ ] **Expected Response** `422 Unprocessable Entity`

### TC-TODO-05 Todo 생성 — 실패 (존재하지 않는 팀)
- [ ] **Endpoint** `POST /teams/999/todos`
- [ ] **Request**
  ```json
  { "title": "테스트" }
  ```
- [ ] **Expected Response** `404 Not Found`
  ```json
  { "detail": "Team not found" }
  ```

### TC-TODO-06 Todo 목록 조회 — 성공 (필터 없음)
- [ ] **Endpoint** `GET /teams/1/todos`
- [ ] **Request** (query 없음)
- [ ] **Expected Response** `200 OK` — Todo 배열 반환

### TC-TODO-07 Todo 목록 조회 — 성공 (status 필터)
- [ ] **Endpoint** `GET /teams/1/todos?status=in_progress`
- [ ] **Request** (body 없음)
- [ ] **Expected Response** `200 OK` — `status: "in_progress"` 인 항목만 반환

### TC-TODO-08 Todo 목록 조회 — 성공 (priority 필터)
- [ ] **Endpoint** `GET /teams/1/todos?priority=high`
- [ ] **Request** (body 없음)
- [ ] **Expected Response** `200 OK` — `priority: "high"` 인 항목만 반환

### TC-TODO-09 Todo 목록 조회 — 성공 (assignee_id 필터)
- [ ] **Endpoint** `GET /teams/1/todos?assignee_id=1`
- [ ] **Request** (body 없음)
- [ ] **Expected Response** `200 OK` — `assignee.id: 1` 인 항목만 반환

### TC-TODO-10 Todo 목록 조회 — 성공 (tag_id 필터)
- [ ] **Endpoint** `GET /teams/1/todos?tag_id=1`
- [ ] **Request** (body 없음)
- [ ] **Expected Response** `200 OK` — 해당 태그가 붙은 항목만 반환

### TC-TODO-11 Todo 단건 조회 — 성공
- [ ] **Endpoint** `GET /teams/1/todos/1`
- [ ] **Request** (body 없음)
- [ ] **Expected Response** `200 OK` — Todo 단건 반환

### TC-TODO-12 Todo 단건 조회 — 실패 (존재하지 않는 Todo)
- [ ] **Endpoint** `GET /teams/1/todos/999`
- [ ] **Request** (body 없음)
- [ ] **Expected Response** `404 Not Found`
  ```json
  { "detail": "Todo not found" }
  ```

### TC-TODO-13 Todo 수정 — 성공 (부분 수정)
- [ ] **Endpoint** `PATCH /teams/1/todos/1`
- [ ] **Request**
  ```json
  { "status": "done" }
  ```
- [ ] **Expected Response** `200 OK` — 수정된 Todo 반환 (`status: "done"`)

### TC-TODO-14 Todo 수정 — 성공 (담당자 변경)
- [ ] **Endpoint** `PATCH /teams/1/todos/1`
- [ ] **Request**
  ```json
  { "assignee_id": 2 }
  ```
- [ ] **Expected Response** `200 OK` — `assignee.id: 2` 로 변경된 Todo 반환

### TC-TODO-15 Todo 수정 — 실패 (존재하지 않는 Todo)
- [ ] **Endpoint** `PATCH /teams/1/todos/999`
- [ ] **Request**
  ```json
  { "status": "done" }
  ```
- [ ] **Expected Response** `404 Not Found`
  ```json
  { "detail": "Todo not found" }
  ```

### TC-TODO-16 Todo 삭제 — 성공
- [ ] **Endpoint** `DELETE /teams/1/todos/1`
- [ ] **Request** (body 없음)
- [ ] **Expected Response** `204 No Content`

### TC-TODO-17 Todo 삭제 — 실패 (존재하지 않는 Todo)
- [ ] **Endpoint** `DELETE /teams/1/todos/999`
- [ ] **Request** (body 없음)
- [ ] **Expected Response** `404 Not Found`
  ```json
  { "detail": "Todo not found" }
  ```

---

## 5. 태그 (Tags)

### TC-TAG-01 태그 생성 — 성공
- [ ] **Endpoint** `POST /teams/1/tags`
- [ ] **Request**
  ```json
  { "name": "backend" }
  ```
- [ ] **Expected Response** `201 Created`
  ```json
  { "id": 1, "name": "backend" }
  ```

### TC-TAG-02 태그 생성 — 실패 (name 누락)
- [ ] **Endpoint** `POST /teams/1/tags`
- [ ] **Request**
  ```json
  {}
  ```
- [ ] **Expected Response** `422 Unprocessable Entity`

### TC-TAG-03 태그 목록 조회 — 성공
- [ ] **Endpoint** `GET /teams/1/tags`
- [ ] **Request** (body 없음)
- [ ] **Expected Response** `200 OK`
  ```json
  [
    { "id": 1, "name": "backend" },
    { "id": 2, "name": "urgent" }
  ]
  ```

### TC-TAG-04 태그 목록 조회 — 빈 목록
- [ ] **Endpoint** `GET /teams/1/tags`
- [ ] **Request** (body 없음, 태그 없는 상태)
- [ ] **Expected Response** `200 OK`
  ```json
  []
  ```

### TC-TAG-05 Todo에 태그 부착 — 성공
- [ ] **Endpoint** `POST /teams/1/todos/1/tags/1`
- [ ] **Request** (body 없음)
- [ ] **Expected Response** `200 OK` — `tags` 배열에 태그 포함된 Todo 반환

### TC-TAG-06 Todo에 태그 부착 — 실패 (존재하지 않는 태그)
- [ ] **Endpoint** `POST /teams/1/todos/1/tags/999`
- [ ] **Request** (body 없음)
- [ ] **Expected Response** `404 Not Found`
  ```json
  { "detail": "Tag not found" }
  ```

### TC-TAG-07 Todo에 태그 부착 — 실패 (이미 부착된 태그)
- [ ] **Endpoint** `POST /teams/1/todos/1/tags/1`
- [ ] **Request** (body 없음, 이미 부착된 상태에서 재요청)
- [ ] **Expected Response** `409 Conflict`
  ```json
  { "detail": "Tag already attached" }
  ```

### TC-TAG-08 Todo에서 태그 제거 — 성공
- [ ] **Endpoint** `DELETE /teams/1/todos/1/tags/1`
- [ ] **Request** (body 없음)
- [ ] **Expected Response** `204 No Content`

### TC-TAG-09 Todo에서 태그 제거 — 실패 (부착되지 않은 태그)
- [ ] **Endpoint** `DELETE /teams/1/todos/1/tags/999`
- [ ] **Request** (body 없음)
- [ ] **Expected Response** `404 Not Found`
  ```json
  { "detail": "Tag not attached to this Todo" }
  ```

---

## 6. Swagger 문서 (F-07)

### TC-SW-01 Swagger UI 접근 — 성공
- [ ] **Endpoint** `GET /docs`
- [ ] **Request** (body 없음)
- [ ] **Expected Response** `200 OK` — Swagger UI HTML 페이지 반환

### TC-SW-02 ReDoc 접근 — 성공
- [ ] **Endpoint** `GET /redoc`
- [ ] **Request** (body 없음)
- [ ] **Expected Response** `200 OK` — ReDoc HTML 페이지 반환

---

## 요약

| 그룹 | 총 케이스 | 성공 | 실패 |
|------|-----------|------|------|
| 유저 | 4 | 2 | 2 |
| 팀 | 4 | 2 | 2 |
| 팀 멤버 | 5 | 2 | 3 |
| Todo CRUD | 17 | 9 | 8 |
| 태그 | 9 | 4 | 5 |
| Swagger | 2 | 2 | 0 |
| **합계** | **41** | **21** | **20** |
