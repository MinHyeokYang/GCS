from typing import List, Optional
import requests

# Thin adapter used by the CLI. Real implementation calls the HTTP API.
# For unit tests these functions can be monkeypatched.


def _url(base: str, path: str) -> str:
    return base.rstrip("/") + path


def get_users(base_url: str) -> List[dict]:
    """Return a list of user dicts by calling GET /users."""
    r = requests.get(_url(base_url, "/users"), timeout=5.0)
    r.raise_for_status()
    return r.json()


def list_todos(team_id: int, base_url: str, status: Optional[str] = None) -> List[dict]:
    """Return a list of todos for a team by calling GET /teams/{team_id}/todos."""
    params = {"status": status} if status else None
    r = requests.get(_url(base_url, f"/teams/{team_id}/todos"), params=params, timeout=5.0)
    r.raise_for_status()
    return r.json()


def create_todo(team_id: int, base_url: str, title: str, description: Optional[str], created_by: int, assignee_id: Optional[int] = None, priority: Optional[str] = None, due_date: Optional[str] = None) -> dict:
    """Create a todo via POST /teams/{team_id}/todos and return the created object."""
    payload = {
        "title": title,
        "description": description,
        "created_by": created_by,
    }
    if assignee_id is not None:
        payload["assignee_id"] = assignee_id
    if priority is not None:
        payload["priority"] = priority
    if due_date is not None:
        payload["due_date"] = due_date

    r = requests.post(_url(base_url, f"/teams/{team_id}/todos"), json=payload, timeout=5.0)
    r.raise_for_status()
    return r.json()


def get_todo(team_id: int, todo_id: int, base_url: str) -> dict:
    r = requests.get(_url(base_url, f"/teams/{team_id}/todos/{todo_id}"), timeout=5.0)
    r.raise_for_status()
    return r.json()


def update_todo(team_id: int, todo_id: int, base_url: str, **kwargs) -> dict:
    r = requests.patch(_url(base_url, f"/teams/{team_id}/todos/{todo_id}"), json=kwargs, timeout=5.0)
    r.raise_for_status()
    return r.json()


def delete_todo(team_id: int, todo_id: int, base_url: str) -> None:
    r = requests.delete(_url(base_url, f"/teams/{team_id}/todos/{todo_id}"), timeout=5.0)
    r.raise_for_status()
    return
