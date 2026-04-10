from typer.testing import CliRunner
from cli.main import app


def test_help_shows_commands():
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "users" in result.output
    assert "todos" in result.output
