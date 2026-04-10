"""Tests for Users API."""

from fastapi.testclient import TestClient


def test_create_user(client: TestClient) -> None:
    """POST /users → 201 with correct body."""
    res = client.post("/users", json={"name": "Alice", "email": "alice@example.com"})
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Alice"
    assert data["email"] == "alice@example.com"
    assert "id" in data
    assert "created_at" in data


def test_create_user_duplicate_email(client: TestClient) -> None:
    """POST /users with duplicate email → 400."""
    payload = {"name": "Alice", "email": "alice@example.com"}
    client.post("/users", json=payload)
    res = client.post("/users", json=payload)
    assert res.status_code == 400


def test_create_user_invalid_email(client: TestClient) -> None:
    """POST /users with invalid email → 422."""
    res = client.post("/users", json={"name": "Bob", "email": "not-an-email"})
    assert res.status_code == 422


def test_list_users_empty(client: TestClient) -> None:
    """GET /users on empty DB → 200 with empty list."""
    res = client.get("/users")
    assert res.status_code == 200
    assert res.json() == []


def test_list_users(client: TestClient) -> None:
    """GET /users returns all created users."""
    client.post("/users", json={"name": "Alice", "email": "alice@example.com"})
    client.post("/users", json={"name": "Bob", "email": "bob@example.com"})
    res = client.get("/users")
    assert res.status_code == 200
    assert len(res.json()) == 2


def test_get_user(client: TestClient) -> None:
    """GET /users/{id} returns a single user."""
    created = client.post("/users", json={"name": "Alice", "email": "alice@example.com"}).json()
    res = client.get(f"/users/{created['id']}")
    assert res.status_code == 200
    assert res.json()["email"] == "alice@example.com"


def test_update_user(client: TestClient) -> None:
    """PATCH /users/{id} updates the user."""
    created = client.post("/users", json={"name": "Alice", "email": "alice@example.com"}).json()
    res = client.patch(f"/users/{created['id']}", json={"name": "Alice Updated"})
    assert res.status_code == 200
    assert res.json()["name"] == "Alice Updated"


def test_delete_user(client: TestClient) -> None:
    """DELETE /users/{id} removes the user."""
    created = client.post("/users", json={"name": "Alice", "email": "alice@example.com"}).json()
    res = client.delete(f"/users/{created['id']}")
    assert res.status_code == 204
    assert client.get(f"/users/{created['id']}").status_code == 404


def test_delete_user_blocked_by_created_todo(client: TestClient) -> None:
    """Deleting a user referenced by Todo.created_by returns 409."""
    user_id = client.post("/users", json={"name": "Alice", "email": "alice@example.com"}).json()["id"]
    team_id = client.post("/teams", json={"name": "Dev Team"}).json()["id"]
    client.post(f"/teams/{team_id}/members", json={"user_id": user_id})
    client.post(f"/teams/{team_id}/todos", json={"title": "T1", "created_by": user_id})

    res = client.delete(f"/users/{user_id}")
    assert res.status_code == 409
