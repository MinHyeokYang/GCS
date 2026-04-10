"""Tests for Todos API."""

from fastapi.testclient import TestClient


def _setup(client: TestClient) -> tuple[int, int]:
    """Create a user, a team, add user as member. Return (user_id, team_id)."""
    user_id = client.post("/users", json={"name": "Alice", "email": "alice@example.com"}).json()["id"]
    team_id = client.post("/teams", json={"name": "Dev"}).json()["id"]
    client.post(f"/teams/{team_id}/members", json={"user_id": user_id})
    return int(user_id), int(team_id)


def _create_todo(client: TestClient, team_id: int, user_id: int, **kwargs: object) -> dict:  # type: ignore[type-arg]
    payload = {"title": "Fix bug", "created_by": user_id, **kwargs}
    return client.post(f"/teams/{team_id}/todos", json=payload).json()


def test_create_todo(client: TestClient) -> None:
    """POST /teams/{id}/todos → 201."""
    user_id, team_id = _setup(client)
    res = client.post(
        f"/teams/{team_id}/todos",
        json={"title": "Fix bug", "created_by": user_id},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["title"] == "Fix bug"
    assert data["status"] == "todo"
    assert data["priority"] == "medium"
    assert data["tags"] == []


def test_create_todo_non_member_creator(client: TestClient) -> None:
    """Creator must be a team member → 400."""
    user_id = client.post("/users", json={"name": "Bob", "email": "bob@example.com"}).json()["id"]
    team_id = client.post("/teams", json={"name": "Dev"}).json()["id"]
    res = client.post(f"/teams/{team_id}/todos", json={"title": "T", "created_by": user_id})
    assert res.status_code == 400


def test_create_todo_non_member_assignee(client: TestClient) -> None:
    """Assignee must be a team member → 400."""
    user_id, team_id = _setup(client)
    outsider_id = client.post("/users", json={"name": "Eve", "email": "eve@example.com"}).json()["id"]
    res = client.post(
        f"/teams/{team_id}/todos",
        json={"title": "T", "created_by": user_id, "assignee_id": outsider_id},
    )
    assert res.status_code == 400


def test_create_todo_invalid_status(client: TestClient) -> None:
    """Invalid status value → 422."""
    user_id, team_id = _setup(client)
    res = client.post(
        f"/teams/{team_id}/todos",
        json={"title": "T", "created_by": user_id, "status": "flying"},
    )
    assert res.status_code == 422


def test_list_todos(client: TestClient) -> None:
    """GET /teams/{id}/todos → 200 list."""
    user_id, team_id = _setup(client)
    _create_todo(client, team_id, user_id)
    _create_todo(client, team_id, user_id, title="Write test")
    res = client.get(f"/teams/{team_id}/todos")
    assert res.status_code == 200
    assert len(res.json()) == 2


def test_list_todos_filter_status(client: TestClient) -> None:
    """Filter by status."""
    user_id, team_id = _setup(client)
    todo_id = _create_todo(client, team_id, user_id)["id"]
    _create_todo(client, team_id, user_id, title="Done task")
    client.patch(f"/teams/{team_id}/todos/{todo_id}", json={"status": "done"})

    res = client.get(f"/teams/{team_id}/todos?status=done")
    assert res.status_code == 200
    assert len(res.json()) == 1


def test_list_todos_filter_priority(client: TestClient) -> None:
    """Filter by priority."""
    user_id, team_id = _setup(client)
    _create_todo(client, team_id, user_id, priority="high")
    _create_todo(client, team_id, user_id)
    res = client.get(f"/teams/{team_id}/todos?priority=high")
    assert len(res.json()) == 1


def test_get_todo(client: TestClient) -> None:
    """GET /teams/{id}/todos/{todo_id} → 200."""
    user_id, team_id = _setup(client)
    todo_id = _create_todo(client, team_id, user_id)["id"]
    res = client.get(f"/teams/{team_id}/todos/{todo_id}")
    assert res.status_code == 200
    assert res.json()["id"] == todo_id


def test_get_todo_not_found(client: TestClient) -> None:
    """Non-existent todo → 404."""
    _, team_id = _setup(client)
    res = client.get(f"/teams/{team_id}/todos/999")
    assert res.status_code == 404


def test_update_todo(client: TestClient) -> None:
    """PATCH updates only specified fields."""
    user_id, team_id = _setup(client)
    todo_id = _create_todo(client, team_id, user_id)["id"]
    res = client.patch(
        f"/teams/{team_id}/todos/{todo_id}",
        json={"status": "in_progress", "priority": "high"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "in_progress"
    assert data["priority"] == "high"
    assert data["title"] == "Fix bug"  # unchanged


def test_delete_todo(client: TestClient) -> None:
    """DELETE → 204, then GET → 404."""
    user_id, team_id = _setup(client)
    todo_id = _create_todo(client, team_id, user_id)["id"]
    res = client.delete(f"/teams/{team_id}/todos/{todo_id}")
    assert res.status_code == 204
    assert client.get(f"/teams/{team_id}/todos/{todo_id}").status_code == 404
