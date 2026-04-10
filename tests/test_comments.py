"""Tests for Comments API."""

from fastapi.testclient import TestClient


def _setup(client: TestClient) -> tuple[int, int, int]:
    """Create creator/commenter users, team, and one todo. Return (team_id, todo_id, commenter_id)."""
    creator_id = client.post("/users", json={"name": "Creator", "email": "creator@example.com"}).json()[
        "id"
    ]
    commenter_id = client.post(
        "/users", json={"name": "Commenter", "email": "commenter@example.com"}
    ).json()["id"]
    team_id = client.post("/teams", json={"name": "Dev Team"}).json()["id"]
    client.post(f"/teams/{team_id}/members", json={"user_id": creator_id})
    client.post(f"/teams/{team_id}/members", json={"user_id": commenter_id})
    todo_id = client.post(
        f"/teams/{team_id}/todos", json={"title": "Todo 1", "created_by": creator_id}
    ).json()["id"]
    return int(team_id), int(todo_id), int(commenter_id)


def test_create_comment(client: TestClient) -> None:
    """POST /comments creates a comment."""
    team_id, todo_id, commenter_id = _setup(client)
    res = client.post(
        f"/teams/{team_id}/todos/{todo_id}/comments",
        json={"user_id": commenter_id, "content": "Looks good"},
    )
    assert res.status_code == 201
    assert res.json()["content"] == "Looks good"


def test_list_comments(client: TestClient) -> None:
    """GET /comments returns comments for the todo."""
    team_id, todo_id, commenter_id = _setup(client)
    client.post(
        f"/teams/{team_id}/todos/{todo_id}/comments",
        json={"user_id": commenter_id, "content": "First"},
    )
    client.post(
        f"/teams/{team_id}/todos/{todo_id}/comments",
        json={"user_id": commenter_id, "content": "Second"},
    )
    res = client.get(f"/teams/{team_id}/todos/{todo_id}/comments")
    assert res.status_code == 200
    assert len(res.json()) == 2


def test_get_update_delete_comment(client: TestClient) -> None:
    """Comment CRUD detail endpoints work."""
    team_id, todo_id, commenter_id = _setup(client)
    created = client.post(
        f"/teams/{team_id}/todos/{todo_id}/comments",
        json={"user_id": commenter_id, "content": "Original"},
    ).json()
    comment_id = created["id"]

    get_res = client.get(f"/teams/{team_id}/todos/{todo_id}/comments/{comment_id}")
    assert get_res.status_code == 200
    assert get_res.json()["content"] == "Original"

    patch_res = client.patch(
        f"/teams/{team_id}/todos/{todo_id}/comments/{comment_id}",
        json={"content": "Updated"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["content"] == "Updated"

    delete_res = client.delete(f"/teams/{team_id}/todos/{todo_id}/comments/{comment_id}")
    assert delete_res.status_code == 204
    assert client.get(f"/teams/{team_id}/todos/{todo_id}/comments/{comment_id}").status_code == 404


def test_comment_author_must_be_team_member(client: TestClient) -> None:
    """Non-member cannot create comments."""
    creator_id = client.post("/users", json={"name": "Creator", "email": "creator@example.com"}).json()[
        "id"
    ]
    outsider_id = client.post("/users", json={"name": "Out", "email": "out@example.com"}).json()["id"]
    team_id = client.post("/teams", json={"name": "Dev Team"}).json()["id"]
    client.post(f"/teams/{team_id}/members", json={"user_id": creator_id})
    todo_id = client.post(
        f"/teams/{team_id}/todos", json={"title": "Todo 1", "created_by": creator_id}
    ).json()["id"]

    res = client.post(
        f"/teams/{team_id}/todos/{todo_id}/comments",
        json={"user_id": outsider_id, "content": "Nope"},
    )
    assert res.status_code == 400


def test_delete_user_cascades_comments(client: TestClient) -> None:
    """Deleting a user removes related comments."""
    team_id, todo_id, commenter_id = _setup(client)
    comment = client.post(
        f"/teams/{team_id}/todos/{todo_id}/comments",
        json={"user_id": commenter_id, "content": "Cascade me"},
    ).json()
    comment_id = comment["id"]

    delete_user_res = client.delete(f"/users/{commenter_id}")
    assert delete_user_res.status_code == 204
    assert client.get(f"/teams/{team_id}/todos/{todo_id}/comments/{comment_id}").status_code == 404
