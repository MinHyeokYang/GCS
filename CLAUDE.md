# CLAUDE.md - Team Todo API Harness

## Project Overview
Team-shared Todo backend built with Python + FastAPI + SQLAlchemy + SQLite.

Core docs:
- `docs/PRD.md`
- `docs/TSD.md`
- `docs/DATABASE.md`
- `docs/TEST_CASE.md`

## Tech Stack
- Framework: FastAPI (`/docs`, `/redoc`, `/openapi.json`)
- ORM: SQLAlchemy 2.0
- DB: SQLite (`todo.db`)
- Migration: Alembic
- Validation: Pydantic v2
- CLI: Typer (`cli/`)
- Python environment/tooling: `uv` / `uvx` (local development standard)

## Directory Snapshot
```text
app/
  main.py
  database.py
  models.py
  schemas.py
  routers/
    users.py
    teams.py
    todos.py
    tags.py
    comments.py
cli/
  main.py
  adapter.py
tests/
  test_users.py
  test_teams.py
  test_todos.py
  test_tags.py
  test_comments.py
  test_cli_*.py
  test_stress_concurrent.py
docs/
alembic/
```

## Coding Standards
- Lint: `ruff check --fix`
- Format: `ruff format`
- Type check: `mypy --strict`
- Tests: `pytest`
- Keep endpoint metadata explicit: `response_model`, `summary`, `status_code`
- Use Google-style docstrings where practical

## Harness Workflow (Planner -> Generator -> Evaluator)
1. Planner
- Confirm scope from `docs/PRD.md`
- Define implementation contract in `docs/sprint_current.md`

2. Generator
- Implement one bounded sprint scope at a time
- Keep model/schema/router/tests aligned

3. Evaluator
- Run tests (`pytest`)
- Validate sprint acceptance checklist
- Mark `PASS` / `FAIL` in `docs/sprint_current.md`

## Sprint Contract Template
```markdown
## Sprint: <name>

### Scope
- [ ] model updates
- [ ] schema updates
- [ ] router updates
- [ ] tests

### Acceptance
- [ ] create endpoint returns 201
- [ ] read endpoint returns 200 with valid schema
- [ ] missing resource returns 404
- [ ] invalid input returns 422

### Result
- Generator: ...
- Evaluator: PASS / FAIL
```

## Local Development with uv
```bash
uv venv
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```
