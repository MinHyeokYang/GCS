# TEST CASES: Team Todo CLI

## Test strategy
- Unit-style tests: use monkeypatching or mocked generated client to test CLI behavior without network.
- Integration tests: start the real dev server (uvicorn app.main:app) and run CLI commands against it.

## Test cases
The test suite covers both unit-level tests (fast, no network) and integration tests (run against a live server). Integration tests are intended to run separately (marked slow) in CI.

### Integration: list todos returns 200 and shows known todo
- Setup: start server with known seeded data (use a pre-populated `todo.db` fixture or run a script that inserts test rows).
- Command: `python -m cli.main todos list --team 1 --base-url http://127.0.0.1:8000`
- Expect: exit code 0, stdout contains a human-friendly table with at least one todo title and its ID.
- Verification steps:
  1. Start server: `uvicorn app.main:app --port 8000` (ensure DB seeded).
  2. Run CLI command.
  3. Assert stdout contains regex like "\d+\s+.+" (id and title).

### Integration: create todo returns 0 and new todo is retrievable
- Command: `python -m cli.main todos create --team 1 --title "cli test" --description "desc" --base-url http://127.0.0.1:8000`
- Expect: exit code 0, CLI prints created ID; subsequent `todos get --team 1 --id <id>` returns the same title.

### Integration: full CRUD flow
- Steps:
  1. Create a todo (capture ID)
  2. Update the todo's title/status
  3. Get the todo and confirm updates
  4. Delete the todo
  5. Get the todo again and expect 404

### Unit: list command formats output
- Mock generated_client. Use monkeypatch to replace the generated client's call with a fake that returns model objects.
- Invoke using typer.testing.CliRunner to call `todos list` with `--team 1`.
- Assert output contains properly formatted lines with id and title.

### Unit: create command sends correct payload
- Monkeypatch the generated client's create method to capture request body.
- Call create command via CliRunner and assert the captured payload includes the provided title and description.

### Test helpers
- Provide fixtures in tests_cli/conftest.py:
  - a fixture to run uvicorn in the background and wait for readiness
  - a fixture to seed the sqlite DB with deterministic data
  - a fixture to provide a CliRunner instance

## CI recommendations
- Run unit tests in the default job.
- Run integration tests in a separate job with a short matrix that starts the server and seeds DB.
- Mark integration tests with pytest.mark.integration or pytest.mark.slow and only run them in nightly or dedicated CI runs.


## CI recommendations
- For integration tests in CI, use TestClient where possible to avoid starting uvicorn; otherwise run uvicorn in background and wait for readiness.
- Mark slow integration tests with pytest mark and run them separately in a dedicated job.

