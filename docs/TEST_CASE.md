# TEST_CASE - Team Todo 백엔드 테스트 체크리스트

업데이트: 2026-04-10

## 1. Users
- [ ] `POST /users` -> `201`
- [ ] 중복 email 생성 -> `400`
- [ ] `GET /users` -> `200`
- [ ] `GET /users/{user_id}` -> `200`/`404`
- [ ] `PATCH /users/{user_id}` -> `200`
- [ ] `DELETE /users/{user_id}` -> `204`
- [ ] `created_by` 참조 사용자 삭제 -> `409`

## 2. Teams / Members
- [ ] `POST /teams` -> `201`
- [ ] `GET /teams` -> `200`
- [ ] `GET /teams/{team_id}` -> `200`/`404`
- [ ] `PATCH /teams/{team_id}` -> `200`
- [ ] `POST /teams/{team_id}/members` -> `201`
- [ ] 중복 멤버 추가 -> `400`
- [ ] 없는 멤버 제거 -> `404`

## 3. Todos
- [ ] `POST /teams/{team_id}/todos` -> `201`
- [ ] status/priority 검증 실패 -> `422`
- [ ] 팀 비멤버 creator/assignee -> `400`
- [ ] `GET /teams/{team_id}/todos` -> `200`
- [ ] 필터(`status`, `priority`, `assignee_id`, `tag_id`) 동작
- [ ] `GET /teams/{team_id}/todos/{todo_id}` -> `200`/`404`
- [ ] `PATCH /teams/{team_id}/todos/{todo_id}` -> `200`
- [ ] `DELETE /teams/{team_id}/todos/{todo_id}` -> `204`

## 4. Tags
- [ ] `POST /teams/{team_id}/tags` -> `201`
- [ ] 같은 팀 중복 태그 -> `400`
- [ ] 다른 팀 동일 태그명 허용
- [ ] `GET /teams/{team_id}/tags` -> `200`
- [ ] `GET /teams/{team_id}/tags/{tag_id}` -> `200`/`404`
- [ ] `PATCH /teams/{team_id}/tags/{tag_id}` -> `200`
- [ ] 태그 부착/해제 -> `201`/`204`

## 5. Comments
- [ ] `POST /teams/{team_id}/todos/{todo_id}/comments` -> `201`
- [ ] 팀 비멤버 댓글 작성 -> `400`
- [ ] `GET /teams/{team_id}/todos/{todo_id}/comments` -> `200`
- [ ] `GET /teams/{team_id}/todos/{todo_id}/comments/{comment_id}` -> `200`/`404`
- [ ] `PATCH /teams/{team_id}/todos/{todo_id}/comments/{comment_id}` -> `200`
- [ ] `DELETE /teams/{team_id}/todos/{todo_id}/comments/{comment_id}` -> `204`
- [ ] 사용자 삭제 시 해당 사용자 댓글 cascade 삭제 확인

## 6. 문서 엔드포인트
- [ ] `GET /docs` -> `200`
- [ ] `GET /redoc` -> `200`
- [ ] `GET /openapi.json` -> `200`
