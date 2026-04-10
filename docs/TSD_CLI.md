# TSD - Team Todo CLI 기술 명세

업데이트: 2026-04-10

## 1. 스택
- Python 3.11+
- Typer
- requests
- pytest + CliRunner

## 2. 실행 규칙
- 엔트리포인트: `python -m cli.main`
- 기본 API 주소: `http://127.0.0.1:8000`
- 주소 우선순위:
1. `--base-url`
2. `TODO_API_BASE`
3. `~/.ttodo.json` (`config set-base-url`)
4. 기본값

## 3. 출력 모드
- 기본: 텍스트 출력
- 옵션: JSON 출력(`--json`)

## 4. 커맨드 매핑
- Users: list/create/get/update/delete
- Teams: list/create/get/update/add-member/remove-member
- Todos: list/create/get/update/delete
- Tags: list/create/get/update/attach/detach
- Comments: list/create/get/update/delete
- Config: show/set-base-url/reset

## 5. 에러 처리
- HTTP 호출 실패 시 `requests.raise_for_status()` 기반 예외 처리
- CLI는 상태코드/오류 내용을 출력하고 종료코드 1로 종료
- 옵션 누락 등 사용 오류는 종료코드 2

## 6. 테스트 전략
- 단위 테스트: 도움말/출력/기본 명령 동작 검증
- 통합 테스트: uvicorn 기동 후 CLI subprocess로 E2E 검증
