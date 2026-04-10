"""Typer-based CLI for Team Todo API."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import typer
from requests import HTTPError

from . import adapter

DEFAULT_BASE_URL = "http://127.0.0.1:8000"
CONFIG_FILE = Path.home() / ".ttodo.json"

app = typer.Typer(help="Team Todo CLI for non-developers and developers.")
users_app = typer.Typer(help="Manage users.")
teams_app = typer.Typer(help="Manage teams and members.")
todos_app = typer.Typer(help="Manage todos.")
tags_app = typer.Typer(help="Manage tags.")
comments_app = typer.Typer(help="Manage todo comments.")
config_app = typer.Typer(help="Manage CLI configuration.")

app.add_typer(users_app, name="users")
app.add_typer(teams_app, name="teams")
app.add_typer(todos_app, name="todos")
app.add_typer(tags_app, name="tags")
app.add_typer(comments_app, name="comments")
app.add_typer(config_app, name="config")


def _load_saved_base_url() -> str | None:
    if not CONFIG_FILE.exists():
        return None
    try:
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    base = data.get("base_url")
    return str(base) if isinstance(base, str) and base.strip() else None


def _save_base_url(base_url: str) -> None:
    CONFIG_FILE.write_text(json.dumps({"base_url": base_url}, indent=2), encoding="utf-8")


def _resolve_base_url(cli_base_url: str | None) -> str:
    if cli_base_url:
        return cli_base_url
    env_base_url = os.getenv("TODO_API_BASE")
    if env_base_url:
        return env_base_url
    file_base_url = _load_saved_base_url()
    if file_base_url:
        return file_base_url
    return DEFAULT_BASE_URL


def _ctx_base_url(ctx: typer.Context) -> str:
    return str(ctx.obj["base_url"])


def _ctx_json(ctx: typer.Context) -> bool:
    return bool(ctx.obj["json"])


def _print_item(item: dict[str, Any]) -> None:
    for key, value in item.items():
        typer.echo(f"{key}: {value}")


def _print_result(ctx: typer.Context, result: Any, *, empty_text: str = "(empty)") -> None:
    if _ctx_json(ctx):
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if result is None:
        typer.echo("OK")
        return
    if isinstance(result, list):
        if not result:
            typer.echo(empty_text)
            return
        for idx, item in enumerate(result):
            if isinstance(item, dict):
                if idx > 0:
                    typer.echo("")
                _print_item(item)
            else:
                typer.echo(str(item))
        return
    if isinstance(result, dict):
        _print_item(result)
        return
    typer.echo(str(result))


def _handle_http_error(err: HTTPError) -> None:
    response = err.response
    if response is None:
        typer.echo(str(err), err=True)
    else:
        try:
            payload = response.json()
            detail = payload.get("detail", payload)
        except ValueError:
            detail = response.text
        typer.echo(f"HTTP {response.status_code}: {detail}", err=True)
    raise typer.Exit(code=1) from err


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    base_url: str | None = typer.Option(
        None,
        "--base-url",
        help="API base URL (default: from env/config, then http://127.0.0.1:8000).",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Print machine-readable JSON output.",
    ),
) -> None:
    """Initialize shared CLI context."""
    resolved_base_url = _resolve_base_url(base_url)
    ctx.obj = {"base_url": resolved_base_url, "json": json_output}
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------


@users_app.command("list")
def users_list(ctx: typer.Context) -> None:
    """List all registered users."""
    try:
        _print_result(ctx, adapter.get_users(_ctx_base_url(ctx)))
    except HTTPError as err:
        _handle_http_error(err)


@users_app.command("create")
def users_create(ctx: typer.Context, name: str = typer.Option(...), email: str = typer.Option(...)) -> None:
    """Create a user."""
    try:
        _print_result(ctx, adapter.create_user(_ctx_base_url(ctx), name, email))
    except HTTPError as err:
        _handle_http_error(err)


@users_app.command("get")
def users_get(ctx: typer.Context, user_id: int = typer.Option(..., "--id")) -> None:
    """Get one user by ID."""
    try:
        _print_result(ctx, adapter.get_user(_ctx_base_url(ctx), user_id))
    except HTTPError as err:
        _handle_http_error(err)


@users_app.command("update")
def users_update(
    ctx: typer.Context,
    user_id: int = typer.Option(..., "--id"),
    name: str | None = typer.Option(None),
    email: str | None = typer.Option(None),
) -> None:
    """Update one user."""
    payload: dict[str, Any] = {}
    if name is not None:
        payload["name"] = name
    if email is not None:
        payload["email"] = email
    if not payload:
        typer.echo("Provide at least one field to update.", err=True)
        raise typer.Exit(code=2)
    try:
        _print_result(ctx, adapter.update_user(_ctx_base_url(ctx), user_id, **payload))
    except HTTPError as err:
        _handle_http_error(err)


@users_app.command("delete")
def users_delete(ctx: typer.Context, user_id: int = typer.Option(..., "--id")) -> None:
    """Delete one user."""
    try:
        adapter.delete_user(_ctx_base_url(ctx), user_id)
        _print_result(ctx, None)
    except HTTPError as err:
        _handle_http_error(err)


# ---------------------------------------------------------------------------
# Teams
# ---------------------------------------------------------------------------


@teams_app.command("list")
def teams_list(ctx: typer.Context) -> None:
    """List teams."""
    try:
        _print_result(ctx, adapter.list_teams(_ctx_base_url(ctx)))
    except HTTPError as err:
        _handle_http_error(err)


@teams_app.command("create")
def teams_create(ctx: typer.Context, name: str = typer.Option(...)) -> None:
    """Create a team."""
    try:
        _print_result(ctx, adapter.create_team(_ctx_base_url(ctx), name))
    except HTTPError as err:
        _handle_http_error(err)


@teams_app.command("get")
def teams_get(ctx: typer.Context, team_id: int = typer.Option(..., "--id")) -> None:
    """Get one team by ID."""
    try:
        _print_result(ctx, adapter.get_team(_ctx_base_url(ctx), team_id))
    except HTTPError as err:
        _handle_http_error(err)


@teams_app.command("update")
def teams_update(
    ctx: typer.Context,
    team_id: int = typer.Option(..., "--id"),
    name: str | None = typer.Option(None),
) -> None:
    """Update one team."""
    if name is None:
        typer.echo("Provide at least one field to update.", err=True)
        raise typer.Exit(code=2)
    try:
        _print_result(ctx, adapter.update_team(_ctx_base_url(ctx), team_id, name=name))
    except HTTPError as err:
        _handle_http_error(err)


@teams_app.command("add-member")
def teams_add_member(
    ctx: typer.Context,
    team_id: int = typer.Option(..., "--team"),
    user_id: int = typer.Option(..., "--user"),
) -> None:
    """Add a user to a team."""
    try:
        _print_result(ctx, adapter.add_member(_ctx_base_url(ctx), team_id, user_id))
    except HTTPError as err:
        _handle_http_error(err)


@teams_app.command("remove-member")
def teams_remove_member(
    ctx: typer.Context,
    team_id: int = typer.Option(..., "--team"),
    user_id: int = typer.Option(..., "--user"),
) -> None:
    """Remove a user from a team."""
    try:
        adapter.remove_member(_ctx_base_url(ctx), team_id, user_id)
        _print_result(ctx, None)
    except HTTPError as err:
        _handle_http_error(err)


# ---------------------------------------------------------------------------
# Todos
# ---------------------------------------------------------------------------


@todos_app.command("list")
def todos_list(
    ctx: typer.Context,
    team_id: int = typer.Option(..., "--team"),
    status: str | None = typer.Option(None),
    priority: str | None = typer.Option(None),
    assignee: int | None = typer.Option(None, "--assignee"),
    tag: int | None = typer.Option(None, "--tag"),
) -> None:
    """List todos for a team."""
    try:
        _print_result(
            ctx,
            adapter.list_todos(
                _ctx_base_url(ctx),
                team_id,
                status=status,
                priority=priority,
                assignee_id=assignee,
                tag_id=tag,
            ),
        )
    except HTTPError as err:
        _handle_http_error(err)


@todos_app.command("create")
def todos_create(
    ctx: typer.Context,
    team_id: int = typer.Option(..., "--team"),
    title: str = typer.Option(...),
    created_by: int = typer.Option(..., "--created-by"),
    description: str | None = typer.Option(None),
    status: str | None = typer.Option(None),
    priority: str | None = typer.Option(None),
    due: str | None = typer.Option(None),
    assignee: int | None = typer.Option(None, "--assignee"),
) -> None:
    """Create a todo."""
    try:
        _print_result(
            ctx,
            adapter.create_todo(
                _ctx_base_url(ctx),
                team_id,
                title=title,
                created_by=created_by,
                description=description,
                status=status,
                priority=priority,
                due_date=due,
                assignee_id=assignee,
            ),
        )
    except HTTPError as err:
        _handle_http_error(err)


@todos_app.command("get")
def todos_get(
    ctx: typer.Context,
    team_id: int = typer.Option(..., "--team"),
    todo_id: int = typer.Option(..., "--id"),
) -> None:
    """Get one todo."""
    try:
        _print_result(ctx, adapter.get_todo(_ctx_base_url(ctx), team_id, todo_id))
    except HTTPError as err:
        _handle_http_error(err)


@todos_app.command("update")
def todos_update(
    ctx: typer.Context,
    team_id: int = typer.Option(..., "--team"),
    todo_id: int = typer.Option(..., "--id"),
    title: str | None = typer.Option(None),
    description: str | None = typer.Option(None),
    status: str | None = typer.Option(None),
    priority: str | None = typer.Option(None),
    due: str | None = typer.Option(None),
    assignee: int | None = typer.Option(None, "--assignee"),
) -> None:
    """Update one todo."""
    payload: dict[str, Any] = {}
    if title is not None:
        payload["title"] = title
    if description is not None:
        payload["description"] = description
    if status is not None:
        payload["status"] = status
    if priority is not None:
        payload["priority"] = priority
    if due is not None:
        payload["due_date"] = due
    if assignee is not None:
        payload["assignee_id"] = assignee
    if not payload:
        typer.echo("Provide at least one field to update.", err=True)
        raise typer.Exit(code=2)
    try:
        _print_result(ctx, adapter.update_todo(_ctx_base_url(ctx), team_id, todo_id, **payload))
    except HTTPError as err:
        _handle_http_error(err)


@todos_app.command("delete")
def todos_delete(
    ctx: typer.Context,
    team_id: int = typer.Option(..., "--team"),
    todo_id: int = typer.Option(..., "--id"),
) -> None:
    """Delete one todo."""
    try:
        adapter.delete_todo(_ctx_base_url(ctx), team_id, todo_id)
        _print_result(ctx, None)
    except HTTPError as err:
        _handle_http_error(err)


# ---------------------------------------------------------------------------
# Tags
# ---------------------------------------------------------------------------


@tags_app.command("list")
def tags_list(ctx: typer.Context, team_id: int = typer.Option(..., "--team")) -> None:
    """List tags in a team."""
    try:
        _print_result(ctx, adapter.list_tags(_ctx_base_url(ctx), team_id))
    except HTTPError as err:
        _handle_http_error(err)


@tags_app.command("create")
def tags_create(
    ctx: typer.Context,
    team_id: int = typer.Option(..., "--team"),
    name: str = typer.Option(...),
) -> None:
    """Create a tag."""
    try:
        _print_result(ctx, adapter.create_tag(_ctx_base_url(ctx), team_id, name))
    except HTTPError as err:
        _handle_http_error(err)


@tags_app.command("get")
def tags_get(
    ctx: typer.Context,
    team_id: int = typer.Option(..., "--team"),
    tag_id: int = typer.Option(..., "--id"),
) -> None:
    """Get one tag."""
    try:
        _print_result(ctx, adapter.get_tag(_ctx_base_url(ctx), team_id, tag_id))
    except HTTPError as err:
        _handle_http_error(err)


@tags_app.command("update")
def tags_update(
    ctx: typer.Context,
    team_id: int = typer.Option(..., "--team"),
    tag_id: int = typer.Option(..., "--id"),
    name: str = typer.Option(...),
) -> None:
    """Update one tag."""
    try:
        _print_result(ctx, adapter.update_tag(_ctx_base_url(ctx), team_id, tag_id, name=name))
    except HTTPError as err:
        _handle_http_error(err)


@tags_app.command("attach")
def tags_attach(
    ctx: typer.Context,
    team_id: int = typer.Option(..., "--team"),
    todo_id: int = typer.Option(..., "--todo"),
    tag_id: int = typer.Option(..., "--tag"),
) -> None:
    """Attach a tag to a todo."""
    try:
        _print_result(ctx, adapter.attach_tag(_ctx_base_url(ctx), team_id, todo_id, tag_id))
    except HTTPError as err:
        _handle_http_error(err)


@tags_app.command("detach")
def tags_detach(
    ctx: typer.Context,
    team_id: int = typer.Option(..., "--team"),
    todo_id: int = typer.Option(..., "--todo"),
    tag_id: int = typer.Option(..., "--tag"),
) -> None:
    """Detach a tag from a todo."""
    try:
        adapter.detach_tag(_ctx_base_url(ctx), team_id, todo_id, tag_id)
        _print_result(ctx, None)
    except HTTPError as err:
        _handle_http_error(err)


# ---------------------------------------------------------------------------
# Comments
# ---------------------------------------------------------------------------


@comments_app.command("list")
def comments_list(
    ctx: typer.Context,
    team_id: int = typer.Option(..., "--team"),
    todo_id: int = typer.Option(..., "--todo"),
) -> None:
    """List comments on a todo."""
    try:
        _print_result(ctx, adapter.list_comments(_ctx_base_url(ctx), team_id, todo_id))
    except HTTPError as err:
        _handle_http_error(err)


@comments_app.command("create")
def comments_create(
    ctx: typer.Context,
    team_id: int = typer.Option(..., "--team"),
    todo_id: int = typer.Option(..., "--todo"),
    user_id: int = typer.Option(..., "--user"),
    content: str = typer.Option(...),
) -> None:
    """Create a comment."""
    try:
        _print_result(
            ctx, adapter.create_comment(_ctx_base_url(ctx), team_id, todo_id, user_id, content)
        )
    except HTTPError as err:
        _handle_http_error(err)


@comments_app.command("get")
def comments_get(
    ctx: typer.Context,
    team_id: int = typer.Option(..., "--team"),
    todo_id: int = typer.Option(..., "--todo"),
    comment_id: int = typer.Option(..., "--id"),
) -> None:
    """Get one comment."""
    try:
        _print_result(ctx, adapter.get_comment(_ctx_base_url(ctx), team_id, todo_id, comment_id))
    except HTTPError as err:
        _handle_http_error(err)


@comments_app.command("update")
def comments_update(
    ctx: typer.Context,
    team_id: int = typer.Option(..., "--team"),
    todo_id: int = typer.Option(..., "--todo"),
    comment_id: int = typer.Option(..., "--id"),
    content: str = typer.Option(...),
) -> None:
    """Update one comment."""
    try:
        _print_result(
            ctx,
            adapter.update_comment(_ctx_base_url(ctx), team_id, todo_id, comment_id, content=content),
        )
    except HTTPError as err:
        _handle_http_error(err)


@comments_app.command("delete")
def comments_delete(
    ctx: typer.Context,
    team_id: int = typer.Option(..., "--team"),
    todo_id: int = typer.Option(..., "--todo"),
    comment_id: int = typer.Option(..., "--id"),
) -> None:
    """Delete one comment."""
    try:
        adapter.delete_comment(_ctx_base_url(ctx), team_id, todo_id, comment_id)
        _print_result(ctx, None)
    except HTTPError as err:
        _handle_http_error(err)


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


@config_app.command("show")
def config_show(ctx: typer.Context) -> None:
    """Show resolved CLI configuration."""
    payload = {
        "base_url": _ctx_base_url(ctx),
        "env_base_url": os.getenv("TODO_API_BASE"),
        "config_file": str(CONFIG_FILE),
        "saved_base_url": _load_saved_base_url(),
    }
    _print_result(ctx, payload)


@config_app.command("set-base-url")
def config_set_base_url(base_url: str = typer.Option(...)) -> None:
    """Save a default base URL in local config file."""
    _save_base_url(base_url)
    typer.echo(f"Saved base URL: {base_url}")


@config_app.command("reset")
def config_reset() -> None:
    """Delete local config file."""
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()
    typer.echo("Config reset.")


if __name__ == "__main__":
    app()
