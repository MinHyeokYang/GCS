"""Tests for Teams API."""

from fastapi.testclient import TestClient


def _create_user(client: TestClient, name: str = "Alice", email: str = "alice@example.com") -> int:
    res = client.post("/users", json={"name": name, "email": email})
    return int(res.json()["id"])


def _create_team(client: TestClient, name: str = "Dev Team") -> int:
    res = client.post("/teams", json={"name": name})
    return int(res.json()["id"])


def test_create_team(client: TestClient) -> None:
    """POST /teams → 201."""
    res = client.post("/teams", json={"name": "Dev Team"})
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Dev Team"
    assert "id" in data


def test_get_team(client: TestClient) -> None:
    """GET /teams/{id} → 200."""
    team_id = _create_team(client)
    res = client.get(f"/teams/{team_id}")
    assert res.status_code == 200
    assert res.json()["id"] == team_id


def test_get_team_not_found(client: TestClient) -> None:
    """GET /teams/999 → 404."""
    res = client.get("/teams/999")
    assert res.status_code == 404


def test_add_member(client: TestClient) -> None:
    """POST /teams/{id}/members → 201."""
    user_id = _create_user(client)
    team_id = _create_team(client)
    res = client.post(f"/teams/{team_id}/members", json={"user_id": user_id})
    assert res.status_code == 201
    data = res.json()
    assert data["team_id"] == team_id
    assert data["user_id"] == user_id


def test_add_member_duplicate(client: TestClient) -> None:
    """Adding the same member twice → 400."""
    user_id = _create_user(client)
    team_id = _create_team(client)
    client.post(f"/teams/{team_id}/members", json={"user_id": user_id})
    res = client.post(f"/teams/{team_id}/members", json={"user_id": user_id})
    assert res.status_code == 400


def test_add_member_team_not_found(client: TestClient) -> None:
    """Adding member to non-existent team → 404."""
    user_id = _create_user(client)
    res = client.post("/teams/999/members", json={"user_id": user_id})
    assert res.status_code == 404


def test_add_member_user_not_found(client: TestClient) -> None:
    """Adding non-existent user → 404."""
    team_id = _create_team(client)
    res = client.post(f"/teams/{team_id}/members", json={"user_id": 999})
    assert res.status_code == 404


def test_remove_member(client: TestClient) -> None:
    """DELETE /teams/{id}/members/{user_id} → 204."""
    user_id = _create_user(client)
    team_id = _create_team(client)
    client.post(f"/teams/{team_id}/members", json={"user_id": user_id})
    res = client.delete(f"/teams/{team_id}/members/{user_id}")
    assert res.status_code == 204


def test_remove_member_not_found(client: TestClient) -> None:
    """Removing non-existent membership → 404."""
    user_id = _create_user(client)
    team_id = _create_team(client)
    res = client.delete(f"/teams/{team_id}/members/{user_id}")
    assert res.status_code == 404
