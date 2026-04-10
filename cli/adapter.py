"""HTTP adapter for Team Todo CLI."""

from typing import Any

import requests


def _url(base: str, path: str) -> str:
    return base.rstrip("/") + path


def _request(
    method: str,
    base_url: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    payload: dict[str, Any] | None = None,
) -> Any:
    response = requests.request(
        method=method,
        url=_url(base_url, path),
        params=params,
        json=payload,
        timeout=10.0,
    )
    response.raise_for_status()
    if response.status_code == 204:
        return None
    return response.json()


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------


def get_users(base_url: str) -> list[dict[str, Any]]:
    return _request("GET", base_url, "/users")


def create_user(base_url: str, name: str, email: str) -> dict[str, Any]:
    return _request("POST", base_url, "/users", payload={"name": name, "email": email})


def get_user(base_url: str, user_id: int) -> dict[str, Any]:
    return _request("GET", base_url, f"/users/{user_id}")


def update_user(base_url: str, user_id: int, **fields: Any) -> dict[str, Any]:
    return _request("PATCH", base_url, f"/users/{user_id}", payload=fields)


def delete_user(base_url: str, user_id: int) -> None:
    _request("DELETE", base_url, f"/users/{user_id}")


# ---------------------------------------------------------------------------
# Teams
# ---------------------------------------------------------------------------


def list_teams(base_url: str) -> list[dict[str, Any]]:
    return _request("GET", base_url, "/teams")


def create_team(base_url: str, name: str) -> dict[str, Any]:
    return _request("POST", base_url, "/teams", payload={"name": name})


def get_team(base_url: str, team_id: int) -> dict[str, Any]:
    return _request("GET", base_url, f"/teams/{team_id}")


def update_team(base_url: str, team_id: int, **fields: Any) -> dict[str, Any]:
    return _request("PATCH", base_url, f"/teams/{team_id}", payload=fields)


def add_member(base_url: str, team_id: int, user_id: int) -> dict[str, Any]:
    return _request(
        "POST", base_url, f"/teams/{team_id}/members", payload={"user_id": user_id}
    )


def remove_member(base_url: str, team_id: int, user_id: int) -> None:
    _request("DELETE", base_url, f"/teams/{team_id}/members/{user_id}")


# ---------------------------------------------------------------------------
# Todos
# ---------------------------------------------------------------------------


def list_todos(
    base_url: str,
    team_id: int,
    *,
    status: str | None = None,
    priority: str | None = None,
    assignee_id: int | None = None,
    tag_id: int | None = None,
) -> list[dict[str, Any]]:
    params: dict[str, Any] = {}
    if status is not None:
        params["status"] = status
    if priority is not None:
        params["priority"] = priority
    if assignee_id is not None:
        params["assignee_id"] = assignee_id
    if tag_id is not None:
        params["tag_id"] = tag_id
    return _request("GET", base_url, f"/teams/{team_id}/todos", params=params or None)


def create_todo(
    base_url: str,
    team_id: int,
    *,
    title: str,
    created_by: int,
    description: str | None = None,
    status: str | None = None,
    priority: str | None = None,
    due_date: str | None = None,
    assignee_id: int | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"title": title, "created_by": created_by}
    if description is not None:
        payload["description"] = description
    if status is not None:
        payload["status"] = status
    if priority is not None:
        payload["priority"] = priority
    if due_date is not None:
        payload["due_date"] = due_date
    if assignee_id is not None:
        payload["assignee_id"] = assignee_id
    return _request("POST", base_url, f"/teams/{team_id}/todos", payload=payload)


def get_todo(base_url: str, team_id: int, todo_id: int) -> dict[str, Any]:
    return _request("GET", base_url, f"/teams/{team_id}/todos/{todo_id}")


def update_todo(base_url: str, team_id: int, todo_id: int, **fields: Any) -> dict[str, Any]:
    return _request("PATCH", base_url, f"/teams/{team_id}/todos/{todo_id}", payload=fields)


def delete_todo(base_url: str, team_id: int, todo_id: int) -> None:
    _request("DELETE", base_url, f"/teams/{team_id}/todos/{todo_id}")


# ---------------------------------------------------------------------------
# Tags
# ---------------------------------------------------------------------------


def list_tags(base_url: str, team_id: int) -> list[dict[str, Any]]:
    return _request("GET", base_url, f"/teams/{team_id}/tags")


def create_tag(base_url: str, team_id: int, name: str) -> dict[str, Any]:
    return _request("POST", base_url, f"/teams/{team_id}/tags", payload={"name": name})


def get_tag(base_url: str, team_id: int, tag_id: int) -> dict[str, Any]:
    return _request("GET", base_url, f"/teams/{team_id}/tags/{tag_id}")


def update_tag(base_url: str, team_id: int, tag_id: int, **fields: Any) -> dict[str, Any]:
    return _request("PATCH", base_url, f"/teams/{team_id}/tags/{tag_id}", payload=fields)


def attach_tag(base_url: str, team_id: int, todo_id: int, tag_id: int) -> dict[str, Any]:
    return _request("POST", base_url, f"/teams/{team_id}/todos/{todo_id}/tags/{tag_id}")


def detach_tag(base_url: str, team_id: int, todo_id: int, tag_id: int) -> None:
    _request("DELETE", base_url, f"/teams/{team_id}/todos/{todo_id}/tags/{tag_id}")


# ---------------------------------------------------------------------------
# Comments
# ---------------------------------------------------------------------------


def list_comments(base_url: str, team_id: int, todo_id: int) -> list[dict[str, Any]]:
    return _request("GET", base_url, f"/teams/{team_id}/todos/{todo_id}/comments")


def create_comment(
    base_url: str, team_id: int, todo_id: int, user_id: int, content: str
) -> dict[str, Any]:
    return _request(
        "POST",
        base_url,
        f"/teams/{team_id}/todos/{todo_id}/comments",
        payload={"user_id": user_id, "content": content},
    )


def get_comment(base_url: str, team_id: int, todo_id: int, comment_id: int) -> dict[str, Any]:
    return _request("GET", base_url, f"/teams/{team_id}/todos/{todo_id}/comments/{comment_id}")


def update_comment(
    base_url: str, team_id: int, todo_id: int, comment_id: int, **fields: Any
) -> dict[str, Any]:
    return _request(
        "PATCH", base_url, f"/teams/{team_id}/todos/{todo_id}/comments/{comment_id}", payload=fields
    )


def delete_comment(base_url: str, team_id: int, todo_id: int, comment_id: int) -> None:
    _request("DELETE", base_url, f"/teams/{team_id}/todos/{todo_id}/comments/{comment_id}")
