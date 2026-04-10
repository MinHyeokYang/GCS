# PRD - Team Todo CLI

업데이트: 2026-04-10

## 1. 목적
백엔드 API를 비대화형 CLI로 호출해 개발자/QA/운영 담당자가 빠르게 검증하고 작업할 수 있게 한다.

## 2. 대상 사용자
- 개발자
- QA
- 운영/기획 담당자(간단한 점검 작업)

## 3. 목표
- 현재 API 엔드포인트 전체 대응(users/teams/todos/tags/comments)
- 사람이 읽기 쉬운 텍스트 출력 + JSON 출력(`--json`)
- 접속 주소 설정(`--base-url`, 환경변수, 로컬 config)
- 명확한 `--help` 설명 제공

## 4. 제외 범위
- TUI/대화형 워크플로우
- 배치 오케스트레이션

## 5. 커맨드 그룹
- `users`
- `teams`
- `todos`
- `tags`
- `comments`
- `config`

## 6. 성공 기준
- 라이브 서버 기준 CRUD 흐름을 CLI로 수행 가능
- 단위 테스트 + E2E 통합 테스트 자동화
