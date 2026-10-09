import json
import re
from pathlib import Path

import pytest
from typer.testing import CliRunner, Result

from shellquest import cli
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


def run(*args: str, input: str | None = None) -> Result:
    return CliRunner().invoke(app, list(args), input=input)


def saved_progress(root: Path) -> dict:
    return json.loads((root / ".shellquest" / "progress.json").read_text())


@pytest.mark.parametrize("command", ["mission", "check", "hint", "list", "goto basics-1"])
def test_mission_commands_need_a_playground(home: Path, command: str) -> None:
    result = run(*command.split())

    assert result.exit_code == 1
    assert "shellquest start" in result.output
    assert not home.exists()


def test_start_shows_the_first_mission(home: Path) -> None:
    result = run("start")

    assert "basics-1 · Hidden in plain sight" in result.output
    assert "Shell basics 1/4" in result.output
    assert "shellquest check <answer>" in result.output


def test_mission_shows_current_mission(playground: Path) -> None:
    result = run("mission")

    assert result.exit_code == 0
    assert "basics-1" in result.output


def test_correct_answer_marks_done_and_moves_on(playground: Path) -> None:
    result = run("check", "saffron")

    assert result.exit_code == 0
    assert "✓ Correct: saffron" in result.output
    assert "Another way:" in result.output
    assert "Why it works:" in result.output
    assert "Next: basics-2 · Count the logs" in result.output
    assert saved_progress(playground)["completed"] == ["basics-1"]
    assert saved_progress(playground)["current"] == "basics-2"


def test_wrong_answer_never_reveals_it(playground: Path) -> None:
    result = run("check", "pepper")

    assert result.exit_code == 1
    assert "Not quite" in result.output
    assert "shellquest hint" in result.output
    assert "saffron" not in result.output
    assert not (playground / ".shellquest" / "progress.json").exists()


def test_check_reads_piped_stdin(playground: Path) -> None:
    result = run("check", input="total 3\n.secret-ingredient\nsaffron\n")

    assert result.exit_code == 0
    assert "✓ Correct: saffron" in result.output


def test_check_with_nothing_piped_is_just_wrong(playground: Path) -> None:
    result = run("check", input="")

    assert result.exit_code == 1
    assert "Not quite" in result.output


def test_check_prompts_when_stdin_is_a_terminal(
    playground: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(cli, "_stdin_is_tty", lambda: True)

    result = run("check", input="saffron\n")

    assert result.exit_code == 0
    assert "✓ Correct" in result.output


def test_macos_padded_wc_output_is_accepted(playground: Path) -> None:
    run("goto", "basics-2")

    result = run("check", input="       7\n")

    assert result.exit_code == 0
    assert "✓ Correct: 7" in result.output


def test_state_mission_inspects_the_playground(playground: Path) -> None:
    run("goto", "basics-3")
    assert run("check").exit_code == 1

    (playground / "notes" / "index.txt").write_text(
        "\n".join(sorted(p.name for p in (playground / "notes").glob("*.md"))) + "\n"
    )
    result = run("check")

    assert result.exit_code == 0
    assert "✓ Correct" in result.output
    assert "Next: basics-4" in result.output


def test_state_mission_does_not_read_stdin(playground: Path) -> None:
    run("goto", "basics-3")

    # Piped input that would be a "wrong answer" for an answer mission must not matter.
    (playground / "notes" / "index.txt").write_text(
        "groceries.md\nideas.md\nmeeting-2024-03.md\nrecipes-to-try.md\ntest-plan.md\n"
    )
    assert run("check", input="garbage").exit_code == 0


def test_last_mission_says_everything_is_done(playground: Path) -> None:
    (playground / "notes" / "index.txt").write_text(
        "\n".join(
            ["groceries.md", "ideas.md", "meeting-2024-03.md", "recipes-to-try.md", "test-plan.md"]
        )
    )
    (playground / "scripts" / "backup.sh").chmod(0o755)
    for mission_id, answer in [
        ("basics-1", "saffron"),
        ("basics-2", "7"),
        ("basics-3", ""),
        ("basics-4", "BACKUP-OK-7731"),
    ]:
        run("goto", mission_id)
        assert run("check", answer).exit_code == 0

    assert "finished every mission" in run("check", "BACKUP-OK-7731").output


def test_hints_are_revealed_one_at_a_time(playground: Path) -> None:
    outputs = [run("hint").output for _ in range(4)]

    for number, output in enumerate(outputs[:3], start=1):
        assert f"Hint {number}/3" in output
    assert "Hint 3/3" in outputs[3]
    assert "all the hints" in outputs[3]
    assert outputs[0] != outputs[1] != outputs[2]
    assert saved_progress(playground)["hints_used"] == {"basics-1": 3}


def test_hint_counts_are_kept_per_mission(playground: Path) -> None:
    run("hint")
    run("goto", "basics-2")

    assert "Hint 1/3" in run("hint").output


def test_list_marks_done_current_and_not_started(playground: Path) -> None:
    run("check", "saffron")

    output = run("list").output

    assert "Shell basics  1/4" in output
    assert re.search(r"✓ basics-1\s+Hidden in plain sight", output)
    assert re.search(r"▶ basics-2\s+Count the logs", output)
    assert re.search(r"· basics-3\s+Make an index", output)
    assert re.search(r"· basics-4\s+Permission denied", output)


def test_goto_changes_current_mission(playground: Path) -> None:
    result = run("goto", "basics-3")

    assert result.exit_code == 0
    assert "basics-3 · Make an index" in result.output
    assert saved_progress(playground)["current"] == "basics-3"


def test_goto_unknown_mission(playground: Path) -> None:
    result = run("goto", "nope-9")

    assert result.exit_code == 1
    assert "shellquest list" in result.output


def test_unknown_saved_mission_falls_back_to_first_unfinished(playground: Path) -> None:
    (playground / ".shellquest" / "progress.json").write_text(
        '{"current": "removed-1", "completed": ["basics-1"], "hints_used": {}}'
    )

    assert "basics-2" in run("mission").output


def test_corrupt_progress_is_reported(playground: Path) -> None:
    (playground / ".shellquest" / "progress.json").write_text("{oops")

    result = run("mission")

    assert result.exit_code == 1
    assert "reset --progress" in result.output
