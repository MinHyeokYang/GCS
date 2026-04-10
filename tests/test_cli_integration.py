import os
import subprocess
import time
import tempfile
import requests
import re
import signal
import sys

import pytest


@pytest.mark.integration
def test_todos_list_and_crud_flow():
    # Create a temporary sqlite file for the server to use
    db_fd, db_path = tempfile.mkstemp(prefix="todo_test_", suffix=".db")
    os.close(db_fd)

    # Set environment to point server to this DB
    env = os.environ.copy()
    env["TODO_DATABASE_URL"] = f"sqlite:///{db_path}"
    port = "8001"
    base = f"http://127.0.0.1:{port}"

    # Start uvicorn server as subprocess
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--port", port, "--host", "127.0.0.1"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        # Wait for server readiness
        deadline = time.time() + 10.0
        ready = False
        while time.time() < deadline:
            try:
                r = requests.get(base + "/docs", timeout=1.0)
                if r.status_code == 200:
                    ready = True
                    break
            except Exception:
                time.sleep(0.2)
        assert ready, "Server did not become ready in time"

        # Run CLI list (expect no todos yet)
        run = subprocess.run([sys.executable, "-m", "cli.main", "todos", "list", "--team", "1", "--base-url", base], capture_output=True, text=True)
        assert run.returncode == 0
        # output may be empty but should not error

        # Create a todo using CLI create (if command exists). Fallback: use API directly
        create = subprocess.run([sys.executable, "-m", "cli.main", "todos", "create", "--team", "1", "--title", "cli test", "--description", "desc", "--base-url", base], capture_output=True, text=True)
        # If CLI doesn't implement create, fallback to API
        if create.returncode != 0:
            # Use API to create
            r = requests.post(base + "/teams/1/todos", json={"title": "cli test", "description": "desc", "created_by": 1})
            assert r.status_code in (200, 201)
            todo_id = r.json().get("id")
        else:
            # Try to parse created ID from CLI output
            m = re.search(r"(\d+)", create.stdout)
            assert m, "CLI did not print created ID"
            todo_id = int(m.group(1))

        # Get the todo via the API and verify title
        g = requests.get(base + f"/teams/1/todos/{todo_id}")
        assert g.status_code == 200
        assert g.json().get("title") == "cli test"

        # Update the todo via API
        patch = requests.patch(base + f"/teams/1/todos/{todo_id}", json={"title": "cli test updated"})
        assert patch.status_code == 200
        assert requests.get(base + f"/teams/1/todos/{todo_id}").json().get("title") == "cli test updated"

        # Delete todo
        d = requests.delete(base + f"/teams/1/todos/{todo_id}")
        assert d.status_code == 200
        assert requests.get(base + f"/teams/1/todos/{todo_id}").status_code == 404

    finally:
        # Terminate server
        proc.send_signal(signal.SIGINT)
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()
        # Cleanup DB file
        try:
            os.remove(db_path)
        except Exception:
            pass
