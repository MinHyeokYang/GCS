## Sprint: CLI E2E tests

### 구현 범위
- [ ] 모델 변경
- [ ] 스키마 추가
- [ ] 라우터 구현
- [x] 테스트 작성

### 완료 기준 (Evaluator 체크리스트)
- [ ] POST /teams/{team_id}/todos → 201 반환
- [ ] GET /teams/{team_id}/todos → 200 + 올바른 JSON 구조
- [ ] 존재하지 않는 리소스 → 404
- [ ] 유효성 오류 → 422

### 결과
- Generator: tests/test_cli_integration.py 추가 (integration tests)
- Evaluator: PENDING


Notes:
- Integration tests marked with @pytest.mark.integration and use a temporary sqlite file so the server subprocess and tests can share DB.
- See docs/TEST_CASE_CLI.md for test scenarios and verification steps.
