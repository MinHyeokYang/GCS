"""Integration tests for CLI end-to-end flow."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import time
from pathlib import Path

import pytest
import requests
from sqlalchemy import create_engine

from app.database import Base


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [os.sys.executable, "-m", "cli.main", *args],
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.integration
def test_todos_list_and_crud_flow() -> None:
    """Run full CLI todo CRUD against a live uvicorn process."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "todo_test.db"
        db_url = f"sqlite:///{db_path}"

        # Initialize schema before launching the API server.
        engine = create_engine(db_url, connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=engine)
        engine.dispose()

        env = os.environ.copy()
        env["TODO_DATABASE_URL"] = db_url
        port = "8001"
        base = f"http://127.0.0.1:{port}"

        proc = subprocess.Popen(
            [os.sys.executable, "-m", "uvicorn", "app.main:app", "--port", port, "--host", "127.0.0.1"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        try:
            deadline = time.time() + 15.0
            while time.time() < deadline:
                try:
                    ready = requests.get(base + "/docs", timeout=1.0)
                    if ready.status_code == 200:
                        break
                except requests.RequestException:
                    time.sleep(0.2)
            else:
                raise AssertionError("Server did not become ready in time")

            # Seed a creator user/team/membership via API.
            user_res = requests.post(
                base + "/users",
                json={"name": "CLI User", "email": "cli.user@example.com"},
                timeout=3.0,
            )
            assert user_res.status_code == 201
            user_id = int(user_res.json()["id"])

            team_res = requests.post(base + "/teams", json={"name": "CLI Team"}, timeout=3.0)
            assert team_res.status_code == 201
            team_id = int(team_res.json()["id"])

            member_res = requests.post(
                base + f"/teams/{team_id}/members",
                json={"user_id": user_id},
                timeout=3.0,
            )
            assert member_res.status_code == 201

            # CLI list before create.
            list_run = _run_cli(
                "--base-url",
                base,
                "todos",
                "list",
                "--team",
                str(team_id),
            )
            assert list_run.returncode == 0, list_run.stderr

            # CLI create.
            create_run = _run_cli(
                "--json",
                "--base-url",
                base,
                "todos",
                "create",
                "--team",
                str(team_id),
                "--title",
                "cli test",
                "--description",
                "desc",
                "--created-by",
                str(user_id),
            )
            assert create_run.returncode == 0, create_run.stderr
            created_todo = json.loads(create_run.stdout)
            todo_id = int(created_todo["id"])

            # CLI update.
            update_run = _run_cli(
                "--json",
                "--base-url",
                base,
                "todos",
                "update",
                "--team",
                str(team_id),
                "--id",
                str(todo_id),
                "--title",
                "cli test updated",
            )
            assert update_run.returncode == 0, update_run.stderr
            updated_todo = json.loads(update_run.stdout)
            assert updated_todo["title"] == "cli test updated"

            # Verify via API.
            get_res = requests.get(base + f"/teams/{team_id}/todos/{todo_id}", timeout=3.0)
            assert get_res.status_code == 200
            assert get_res.json()["title"] == "cli test updated"

            # CLI delete.
            delete_run = _run_cli(
                "--base-url",
                base,
                "todos",
                "delete",
                "--team",
                str(team_id),
                "--id",
                str(todo_id),
            )
            assert delete_run.returncode == 0, delete_run.stderr
            assert requests.get(base + f"/teams/{team_id}/todos/{todo_id}", timeout=3.0).status_code == 404
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
