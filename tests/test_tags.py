"""Tests for Tags API and Todo tag attachment."""

from fastapi.testclient import TestClient


def _setup(client: TestClient) -> tuple[int, int]:
    """Create a user, a team, add user as member. Return (user_id, team_id)."""
    user_id = client.post("/users", json={"name": "Alice", "email": "alice@example.com"}).json()["id"]
    team_id = client.post("/teams", json={"name": "Dev"}).json()["id"]
    client.post(f"/teams/{team_id}/members", json={"user_id": user_id})
    return int(user_id), int(team_id)


def _create_tag(client: TestClient, team_id: int, name: str = "backend") -> int:
    return int(client.post(f"/teams/{team_id}/tags", json={"name": name}).json()["id"])


def _create_todo(client: TestClient, team_id: int, user_id: int) -> int:
    return int(
        client.post(f"/teams/{team_id}/todos", json={"title": "Fix bug", "created_by": user_id}).json()["id"]
    )


def test_create_tag(client: TestClient) -> None:
    """POST /teams/{id}/tags → 201."""
    _, team_id = _setup(client)
    res = client.post(f"/teams/{team_id}/tags", json={"name": "backend"})
    assert res.status_code == 201
    assert res.json()["name"] == "backend"
    assert res.json()["team_id"] == team_id


def test_create_tag_duplicate(client: TestClient) -> None:
    """Duplicate tag name within same team → 400."""
    _, team_id = _setup(client)
    client.post(f"/teams/{team_id}/tags", json={"name": "backend"})
    res = client.post(f"/teams/{team_id}/tags", json={"name": "backend"})
    assert res.status_code == 400


def test_create_tag_same_name_different_team(client: TestClient) -> None:
    """Same tag name in different teams is allowed."""
    _, team_id1 = _setup(client)
    user_id2 = client.post("/users", json={"name": "Bob", "email": "bob@example.com"}).json()["id"]
    team_id2 = client.post("/teams", json={"name": "Ops"}).json()["id"]
    client.post(f"/teams/{team_id2}/members", json={"user_id": user_id2})

    assert client.post(f"/teams/{team_id1}/tags", json={"name": "backend"}).status_code == 201
    assert client.post(f"/teams/{team_id2}/tags", json={"name": "backend"}).status_code == 201


def test_list_tags(client: TestClient) -> None:
    """GET /teams/{id}/tags → 200 list."""
    _, team_id = _setup(client)
    _create_tag(client, team_id, "backend")
    _create_tag(client, team_id, "frontend")
    res = client.get(f"/teams/{team_id}/tags")
    assert res.status_code == 200
    assert len(res.json()) == 2


def test_get_tag(client: TestClient) -> None:
    """GET /teams/{id}/tags/{tag_id} returns one tag."""
    _, team_id = _setup(client)
    tag_id = _create_tag(client, team_id, "backend")
    res = client.get(f"/teams/{team_id}/tags/{tag_id}")
    assert res.status_code == 200
    assert res.json()["id"] == tag_id


def test_update_tag(client: TestClient) -> None:
    """PATCH /teams/{id}/tags/{tag_id} updates tag name."""
    _, team_id = _setup(client)
    tag_id = _create_tag(client, team_id, "backend")
    res = client.patch(f"/teams/{team_id}/tags/{tag_id}", json={"name": "api"})
    assert res.status_code == 200
    assert res.json()["name"] == "api"


def test_attach_tag(client: TestClient) -> None:
    """POST attach tag → todo response contains the tag."""
    user_id, team_id = _setup(client)
    todo_id = _create_todo(client, team_id, user_id)
    tag_id = _create_tag(client, team_id)
    res = client.post(f"/teams/{team_id}/todos/{todo_id}/tags/{tag_id}")
    assert res.status_code == 201
    tags = res.json()["tags"]
    assert any(t["id"] == tag_id for t in tags)


def test_attach_tag_wrong_team(client: TestClient) -> None:
    """Tag from another team cannot be attached → 404."""
    user_id, team_id = _setup(client)
    todo_id = _create_todo(client, team_id, user_id)

    user_id2 = client.post("/users", json={"name": "Bob", "email": "bob@example.com"}).json()["id"]
    team_id2 = client.post("/teams", json={"name": "Ops"}).json()["id"]
    client.post(f"/teams/{team_id2}/members", json={"user_id": user_id2})
    other_tag_id = _create_tag(client, team_id2, "ops-tag")

    res = client.post(f"/teams/{team_id}/todos/{todo_id}/tags/{other_tag_id}")
    assert res.status_code == 404


def test_attach_tag_duplicate(client: TestClient) -> None:
    """Attaching the same tag twice → 400."""
    user_id, team_id = _setup(client)
    todo_id = _create_todo(client, team_id, user_id)
    tag_id = _create_tag(client, team_id)
    client.post(f"/teams/{team_id}/todos/{todo_id}/tags/{tag_id}")
    res = client.post(f"/teams/{team_id}/todos/{todo_id}/tags/{tag_id}")
    assert res.status_code == 400


def test_detach_tag(client: TestClient) -> None:
    """DELETE tag from todo → 204, tag no longer in list."""
    user_id, team_id = _setup(client)
    todo_id = _create_todo(client, team_id, user_id)
    tag_id = _create_tag(client, team_id)
    client.post(f"/teams/{team_id}/todos/{todo_id}/tags/{tag_id}")

    res = client.delete(f"/teams/{team_id}/todos/{todo_id}/tags/{tag_id}")
    assert res.status_code == 204

    todo = client.get(f"/teams/{team_id}/todos/{todo_id}").json()
    assert all(t["id"] != tag_id for t in todo["tags"])


def test_detach_tag_not_attached(client: TestClient) -> None:
    """Detaching a tag that isn't attached → 404."""
    user_id, team_id = _setup(client)
    todo_id = _create_todo(client, team_id, user_id)
    tag_id = _create_tag(client, team_id)
    res = client.delete(f"/teams/{team_id}/todos/{todo_id}/tags/{tag_id}")
    assert res.status_code == 404


def test_list_todos_filter_by_tag(client: TestClient) -> None:
    """GET /todos?tag_id= filters correctly."""
    user_id, team_id = _setup(client)
    todo_id = _create_todo(client, team_id, user_id)
    _create_todo(client, team_id, user_id)  # untagged todo
    tag_id = _create_tag(client, team_id)
    client.post(f"/teams/{team_id}/todos/{todo_id}/tags/{tag_id}")

    res = client.get(f"/teams/{team_id}/todos?tag_id={tag_id}")
    assert res.status_code == 200
    result = res.json()
    assert len(result) == 1
    assert result[0]["id"] == todo_id
