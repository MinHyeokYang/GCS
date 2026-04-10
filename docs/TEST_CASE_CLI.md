# TEST_CASE_CLI - Team Todo CLI 테스트 체크리스트

업데이트: 2026-04-10

## 1. 단위 테스트
- [ ] `--help`에서 커맨드 그룹(users/teams/todos/tags/comments/config) 노출
- [ ] `users list` 출력 포맷 정상
- [ ] 필수 옵션 누락 시 종료코드 `2`

## 2. 통합(E2E) 테스트
- [ ] 임시 SQLite DB + uvicorn 서버 기동
- [ ] API로 user/team/member seed
- [ ] `todos list` 성공(종료코드 `0`)
- [ ] `--json todos create` 결과 JSON 파싱 가능
- [ ] `todos update` 후 값 변경 확인
- [ ] `todos delete` 후 API 조회 `404`

## 3. 설정(config) 테스트
- [ ] `config set-base-url`로 주소 저장
- [ ] `config show`에서 해석된 주소 확인
- [ ] `config reset`으로 설정 삭제
