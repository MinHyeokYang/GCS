# TSD: Team Todo CLI Technical Spec

**언어:** 한국어 | **대상:** 개발자 · CLI 사용자 | **마지막 수정:** 2026-04-10



## Overview
This document specifies the technical design for a CLI that wraps the Team Todo API. It describes tools, runtime behavior, file layout, and the mapping between CLI commands and OpenAPI operations.

## Tools
- Codegen: openapi-python-client (https://github.com/openapi-generators/openapi-python-client)
- CLI framework: Typer
- HTTP: generated client uses httpx
- Testing: pytest, typer.testing.CliRunner

## File layout
- generated_client/  (checked-in, output of openapi-python-client)
- cli/
  - __main__.py
  - main.py  (Typer app)
- tests_cli/
  - test_cli_integration.py
  - test_cli_unit.py
- docs/
  - PRD_CLI.md
  - TSD_CLI.md
  - TEST_CASE_CLI.md

## Configuration
- Environment variables:
  - TODO_API_BASE (default: http://127.0.0.1:8000)
  - TODO_API_KEY
- CLI flags override env vars; Typer Option envvar parameter used for convenience.

## Command mapping (examples)
The CLI will expose a complete mapping from commands to API endpoints. Commands are grouped by resource (users, teams, todos, tags). Below are the concrete CLI commands and which API endpoints they call. All commands accept `--base-url` and `--api-key` (or use env vars TODO_API_BASE and TODO_API_KEY).

- todos list --team <team_id> [--status <open|in_progress|done>] [--priority <low|medium|high>] [--assignee <user_id>] [--tag <tag_id>]
  - Calls: GET /teams/{team_id}/todos
  - Description: List todos for a team; optional filters by status, priority, assignee, or tag.

- todos get --team <team_id> --id <todo_id>
  - Calls: GET /teams/{team_id}/todos/{todo_id}
  - Description: Show a single todo's details.

- todos create --team <team_id> --title <text> [--description <text>] [--assignee <user_id>] [--priority <low|medium|high>] [--due <YYYY-MM-DD>]
  - Calls: POST /teams/{team_id}/todos
  - Description: Create a new todo in the team.

- todos update --team <team_id> --id <todo_id> [--title] [--description] [--status] [--priority] [--assignee] [--due]
  - Calls: PATCH /teams/{team_id}/todos/{todo_id}
  - Description: Partially update a todo. Only provided flags are changed.

- todos delete --team <team_id> --id <todo_id>
  - Calls: DELETE /teams/{team_id}/todos/{todo_id}
  - Description: Permanently remove a todo.

- tags list --team <team_id>
  - Calls: GET /teams/{team_id}/tags
  - Description: List tags for the given team.

- tags create --team <team_id> --name <name>
  - Calls: POST /teams/{team_id}/tags
  - Description: Create a new tag for the team.

- tags attach --team <team_id> --todo <todo_id> --tag <tag_id>
  - Calls: POST /teams/{team_id}/todos/{todo_id}/tags/{tag_id}
  - Description: Attach a tag to a todo.

- tags detach --team <team_id> --todo <todo_id> --tag <tag_id>
  - Calls: DELETE /teams/{team_id}/todos/{todo_id}/tags/{tag_id}
  - Description: Detach a tag from a todo.

- teams create --name <name>
  - Calls: POST /teams
  - Description: Create a new team.

- teams get --id <team_id>
  - Calls: GET /teams/{team_id}
  - Description: Get details for a team.

- teams add-member --team <team_id> --user <user_id>
  - Calls: POST /teams/{team_id}/members
  - Description: Add an existing user to a team.

- teams remove-member --team <team_id> --user <user_id>
  - Calls: DELETE /teams/{team_id}/members/{user_id}
  - Description: Remove a user from a team.

- users list
  - Calls: GET /users
  - Description: List all users.

- users create --name <name> --email <email>
  - Calls: POST /users
  - Description: Create a new user.




## Client integration notes
- The generated client will be imported as `generated_client` and a thin wrapper function will adapt default headers (Authorization).
- If method names from codegen differ, only cli/main.py will require minimal adaptation.

## Runtime
- CLI is a local developer tool; run via `python -m cli.main [resource] [command]` or install as console script.

