from typer.testing import CliRunner
from cli import adapter
from cli.main import app


def test_users_list_formats_output(monkeypatch):
    runner = CliRunner()

    def fake_get_users(base_url: str):
        return [{"id": 1, "name": "Alice", "email": "alice@example.com"}]

    monkeypatch.setattr(adapter, "get_users", fake_get_users)
    result = runner.invoke(app, ["users", "list"])
    assert result.exit_code == 0
    assert "Alice" in result.output
