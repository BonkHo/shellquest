import re
from pathlib import Path

import pytest
from typer.testing import CliRunner

from shellquest.cli import app

COMMANDS = ["start", "mission", "check", "hint", "list", "goto", "reset"]


def test_help_lists_all_commands() -> None:
    result = CliRunner().invoke(app, ["--help"])

    assert result.exit_code == 0
    for command in COMMANDS:
        # Match the name at the start of a row in the Commands table, not anywhere in the help text.
        assert re.search(rf"^\W*{command}\s", result.output, re.MULTILINE), command


def test_start_builds_playground(home: Path) -> None:
    result = CliRunner().invoke(app, ["start"])

    assert result.exit_code == 0
    assert (home / ".shellquest" / "marker").is_file()
    assert f"cd {home}" in result.output


def test_start_does_not_rebuild(playground: Path) -> None:
    secret = playground / ".secret-ingredient"
    secret.write_text("changed")

    result = CliRunner().invoke(app, ["start"])

    assert result.exit_code == 0
    assert "already" in result.output
    assert secret.read_text() == "changed"


def test_start_refuses_unmarked_folder(home: Path) -> None:
    home.mkdir()
    (home / "keep.txt").write_text("mine")

    result = CliRunner().invoke(app, ["start"])

    assert result.exit_code == 1
    assert sorted(p.name for p in home.iterdir()) == ["keep.txt"]


def test_reset_declined_changes_nothing(playground: Path) -> None:
    secret = playground / ".secret-ingredient"
    secret.write_text("changed")

    result = CliRunner().invoke(app, ["reset"], input="n\n")

    assert result.exit_code == 1  # typer.confirm(abort=True) exits with 1
    assert secret.read_text() == "changed"


@pytest.mark.parametrize(("args", "user_input"), [(["reset"], "y\n"), (["reset", "--yes"], None)])
def test_reset_rebuilds(playground: Path, args: list[str], user_input: str | None) -> None:
    secret = playground / ".secret-ingredient"
    secret.write_text("changed")

    result = CliRunner().invoke(app, args, input=user_input)

    assert result.exit_code == 0
    assert secret.read_text() == "saffron\n"


def test_reset_progress_clears_progress(playground: Path) -> None:
    progress = playground / ".shellquest" / "progress.json"
    progress.write_text("{}")

    result = CliRunner().invoke(app, ["reset", "--yes", "--progress"])

    assert result.exit_code == 0
    assert not progress.exists()


def test_reset_refuses_unmarked_folder(home: Path) -> None:
    home.mkdir()
    (home / "keep.txt").write_text("mine")

    result = CliRunner().invoke(app, ["reset", "--yes"])

    assert result.exit_code == 1
    assert (home / "keep.txt").read_text() == "mine"
