from typing import List, Optional
import os
import typer

app = typer.Typer()

# thin adapter import
from . import adapter

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        typer.echo("Team Todo CLI. Use --help for commands.")

users_app = typer.Typer()
app.add_typer(users_app, name="users")

todos_app = typer.Typer()
app.add_typer(todos_app, name="todos")

@users_app.command("list")
def users_list(base_url: Optional[str] = typer.Option(None, envvar="TODO_API_BASE")):
    """List users"""
    base = base_url or os.getenv("TODO_API_BASE", "http://127.0.0.1:8000")
    users = adapter.get_users(base)
    for u in users:
        typer.echo(f"{u['id']}: {u['name']} <{u['email']}>")

@todos_app.command("list")
def todos_list(team: int = typer.Option(..., help="Team ID"),
               base_url: Optional[str] = typer.Option(None, envvar="TODO_API_BASE")):
    """List todos for a team"""
    base = base_url or os.getenv("TODO_API_BASE", "http://127.0.0.1:8000")
    todos = adapter.list_todos(team, base)
    if not todos:
        typer.echo("(no todos)")
        return
    for t in todos:
        typer.echo(f"{t['id']}\t{t['title']}")


@todos_app.command("create")
def todos_create(team: int = typer.Option(..., help="Team ID"),
                 title: str = typer.Option(...),
                 description: Optional[str] = typer.Option(None),
                 created_by: int = typer.Option(...),
                 assignee: Optional[int] = typer.Option(None),
                 priority: Optional[str] = typer.Option(None),
                 due: Optional[str] = typer.Option(None),
                 base_url: Optional[str] = typer.Option(None, envvar="TODO_API_BASE")):
    """Create a todo in the team"""
    base = base_url or os.getenv("TODO_API_BASE", "http://127.0.0.1:8000")
    todo = adapter.create_todo(team, base, title, description, created_by, assignee, priority, due)
    typer.echo(str(todo.get("id")))

if __name__ == "__main__":
    app()
