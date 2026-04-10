# PRD: Team Todo CLI

## Purpose
Provide a simple, user-friendly command-line client for the Team Todo API so both developers and non-developers (QA, product managers, automation engineers) can interact with the service without writing code.

## Audience
- Developers who want a quick CLI for local testing
- QA engineers who need to run reproducible test steps
- Product owners or support staff who need to inspect or create data without a browser

## Key user stories
- As a QA engineer, I can list all todos for a team and filter by status so I can verify workflow states.
- As a developer, I can create and update todos from the terminal when debugging.
- As a support agent, I can add/remove users from teams and attach tags to todos without opening the API docs.

## Features (plain-English)
The CLI exposes commands that map directly to every API endpoint. Commands are grouped by resource and written so non-developers understand them.

Core commands examples:
- todos list --team 5 --status open
  - "Show all todos for team #5, only those that are open."
- todos get --team 5 --id 12
  - "Show details for todo #12 in team #5."
- todos create --team 5 --title "Fix login" --description "Users can't sign in"
  - "Create a new todo in team #5 with the given title and description."
- todos update --team 5 --id 12 --title "Fix login bug" --status done
  - "Change title or status (only provided fields change)."
- todos delete --team 5 --id 12
  - "Permanently delete todo #12 from team #5."

Team and member commands:
- teams create --name "Mobile"
  - "Create a new team called Mobile."
- teams get --id 3
  - "Show team #3 details."
- teams add-member --team 3 --user 7
  - "Add user #7 to team #3."
- teams remove-member --team 3 --user 7
  - "Remove user #7 from team #3."

User commands:
- users list
  - "Show all registered users."
- users create --name "Alice" --email "alice@example.com"
  - "Create a new user with a name and email."

Tag commands (team-scoped):
- tags list --team 5
  - "Show all tags in team #5."
- tags create --team 5 --name "urgent"
  - "Create a tag called 'urgent' in team #5."
- tags attach --team 5 --todo 12 --tag 4
  - "Attach tag #4 to todo #12 in team #5."
- tags detach --team 5 --todo 12 --tag 4
  - "Remove tag #4 from todo #12 in team #5."

## Configuration and auth (plain-English)
- By default the CLI talks to your local dev server at http://127.0.0.1:8000.
- You can change the server with --base-url or by setting TODO_API_BASE.
- If the API requires a key, set TODO_API_KEY or pass --api-key when running commands.

## Success criteria
- The CLI supports all endpoints in the API and provides clear help text explaining what each command does in plain English.
- Each command has automated tests that run in CI (unit and integration) and validate expected behavior.



## Purpose
Provide a simple, typed command-line client for the Team Todo API so developers and automation can interact with the service without writing HTTP code.

## Goals
- Expose common resources as subcommands: users, teams, todos, tags.
- Support listing, retrieving, creating, updating, and deleting where the API supports it.
- Use a generated typed client (openapi-python-client) to ensure request/response models match the server.
- Configurable base URL and API key via env vars or CLI flags.
- Ship checked-in generated client under `generated_client/` for reproducibility.

## Non-goals
- Not intended to replace SDKs for programmatic consumption.
- Not intended to implement advanced scripting features.

## Success criteria
- CLI can list and create todos on a local dev server.
- Tests validate common workflows and run in CI.

## Stakeholders
- Backend developers
- QA engineers
- Automation / CI engineers
