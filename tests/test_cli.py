import re

from typer.testing import CliRunner

from shellquest.cli import app

COMMANDS = ["start", "mission", "check", "hint", "list", "goto", "reset"]


def test_help_lists_all_commands() -> None:
    result = CliRunner().invoke(app, ["--help"])

    assert result.exit_code == 0
    for command in COMMANDS:
        # Match the name at the start of a row in the Commands table, not anywhere in the help text.
        assert re.search(rf"^\W*{command}\s", result.output, re.MULTILINE), command
