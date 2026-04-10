# Team Todo API + CLI 사용 가이드

팀 단위 Todo 백엔드(FastAPI)와 CLI(Typer)를 함께 사용하는 저장소입니다.

## 1. 빠른 시작

### 1-1. 개발 환경 준비
```bash
uv venv
uv sync
```

### 1-2. DB 마이그레이션
```bash
uv run alembic upgrade head
```

### 1-3. 서버 실행
```bash
uv run uvicorn app.main:app --reload
```

### 1-4. 문서 확인
- Swagger: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- OpenAPI: `http://127.0.0.1:8000/openapi.json`

## 2. 테스트 실행

### 2-1. 전체 테스트
```bash
uv run pytest -q
```

### 2-2. E2E(통합)만 실행
```bash
uv run pytest -q -m integration
```

## 3. CLI 사용법

CLI 진입:
```bash
uv run python -m cli.main --help
```

공통 옵션:
- `--base-url`: 대상 API 주소 지정
- `--json`: JSON 출력 모드

### 3-1. 사용자/팀 준비
```bash
uv run python -m cli.main users create --name "Alice" --email "alice@example.com"
uv run python -m cli.main teams create --name "Dev Team"
uv run python -m cli.main teams add-member --team 1 --user 1
```

### 3-2. Todo 생성/조회/수정/삭제
```bash
uv run python -m cli.main todos create --team 1 --title "API 명세 작성" --created-by 1
uv run python -m cli.main --json todos list --team 1
uv run python -m cli.main todos update --team 1 --id 1 --status in_progress
uv run python -m cli.main todos delete --team 1 --id 1
```

### 3-3. 태그/댓글
```bash
uv run python -m cli.main tags create --team 1 --name backend
uv run python -m cli.main tags attach --team 1 --todo 1 --tag 1
uv run python -m cli.main comments create --team 1 --todo 1 --user 1 --content "검토 부탁해요."
```

### 3-4. CLI 기본 주소 저장
```bash
uv run python -m cli.main config set-base-url --base-url http://127.0.0.1:8000
uv run python -m cli.main config show
```

## 4. 문서 안내

핵심 문서:
- 제품 요구사항: `docs/PRD.md`
- 기술 명세: `docs/TSD.md`
- DB 명세: `docs/DATABASE.md`
- 백엔드 테스트 케이스: `docs/TEST_CASE.md`
- CLI 요구사항: `docs/PRD_CLI.md`
- CLI 기술 명세: `docs/TSD_CLI.md`
- CLI 테스트 케이스: `docs/TEST_CASE_CLI.md`
- Harness 운영 방식: `docs/HARNESS.md`

## 5. 품질 게이트
- 린트/포맷: Ruff
- 타입체크: mypy (strict)
- 테스트: pytest
- pre-commit 훅에서 `pytest -m "not integration"` 실행
