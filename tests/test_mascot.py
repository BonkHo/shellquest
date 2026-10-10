from pathlib import Path

import pytest
from rich.console import Console
from typer.testing import CliRunner, Result

from shellquest import mascot, missions
from shellquest.cli import app

SHELL_ART = r"`-.___.-'"  # the bottom of the shell, present in every mood
SHELL_WIDTH = 13


def run(*args: str) -> Result:
    return CliRunner().invoke(app, list(args))


@pytest.fixture
def started(home: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A built playground with the mascot forced on (CliRunner output is never a terminal)."""
    monkeypatch.setenv("SHELLQUEST_MASCOT", "1")
    assert run("start").exit_code == 0
    return home


def test_is_enabled_explicit_setting_wins() -> None:
    console = Console(force_terminal=True)
    piped = Console(force_terminal=False)

    assert mascot.is_enabled(False, console) is False
    assert mascot.is_enabled(True, piped) is True


def test_is_enabled_automatic_follows_terminal() -> None:
    assert mascot.is_enabled(None, Console(force_terminal=True)) is True
    assert mascot.is_enabled(None, Console(force_terminal=False)) is False


@pytest.mark.parametrize("mood", mascot.MOODS)
def test_render_draws_shell_and_bubble(mood: mascot.Mood) -> None:
    rows = mascot.render(mood, "basics-1")

    assert any(SHELL_ART in row for row in rows)
    assert mascot.FACES[mood] in "\n".join(rows)
    assert mascot.line_for(mood, "basics-1") in "\n".join(rows)  # short enough not to wrap


@pytest.mark.parametrize("mood", mascot.MOODS)
def test_shell_is_left_right_symmetrical(mood: mascot.Mood) -> None:
    # Draw only the shell (the first 4 rows, the first 13 columns), with the face blanked out.
    rows = [row[:SHELL_WIDTH].ljust(SHELL_WIDTH) for row in mascot.render(mood, "basics-1")[:4]]
    # A ` on the left mirrors a ' on the right, and / mirrors \.
    same_quote = str.maketrans("`", "'")
    swap_slash = str.maketrans("/\\", "\\/")

    for row in rows:
        row = row.replace(mascot.FACES[mood], "   ").translate(same_quote)
        assert row == row[::-1].translate(swap_slash), row


@pytest.mark.parametrize("mood", mascot.MOODS)
def test_line_for_is_deterministic_and_from_the_pool(mood: mascot.Mood) -> None:
    assert mascot.line_for(mood, "git-2:1") == mascot.line_for(mood, "git-2:1")
    assert mascot.line_for(mood, "git-2:1") in mascot.LINES[mood]


def test_every_phrase_fits_on_one_line() -> None:
    for pool in mascot.LINES.values():
        assert all(len(line) <= mascot.BUBBLE_WIDTH for line in pool)


def test_phrases_never_contain_an_answer() -> None:
    """No phrase may give anything away (SPEC: never reveal the answer)."""
    phrases = [line for pool in mascot.LINES.values() for line in pool]
    for mission in missions.all_missions():
        secrets = {mission.solution.lower(), mission.id.lower()}
        for phrase in phrases:
            assert not any(secret in phrase.lower() for secret in secrets), (mission.id, phrase)


def test_mission_hello(started: Path) -> None:
    result = run("mission")

    assert SHELL_ART in result.output
    assert "Mission basics-1" in result.output  # original output is untouched


def test_wrong_answer_oops_and_still_fails(started: Path) -> None:
    result = run("check", "nutmeg")

    assert result.exit_code == 1
    assert "Not quite" in result.output
    assert SHELL_ART in result.output
    assert "saffron" not in result.output


def test_right_answer_cheers_after_next_line(started: Path) -> None:
    result = run("check", "saffron")

    assert result.exit_code == 0
    assert "✓ Correct: saffron" in result.output
    assert result.output.index("Next: basics-2") < result.output.index(SHELL_ART)


def test_hint_shell_speaks(started: Path) -> None:
    result = run("hint")

    assert "Hint 1/" in result.output
    assert SHELL_ART in result.output


def test_finishing_the_last_mission_says_done(
    started: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(missions, "next_after", lambda *_: None)

    result = run("check", "saffron")

    assert "finished every mission" in result.output
    assert mascot.line_for("done", "basics-1") in result.output


@pytest.mark.parametrize("off", [["--no-mascot"], []])
def test_can_be_turned_off(started: Path, monkeypatch: pytest.MonkeyPatch, off: list[str]) -> None:
    if not off:  # the environment variable route
        monkeypatch.setenv("SHELLQUEST_MASCOT", "0")

    result = run(*off, "mission")

    assert result.exit_code == 0
    assert SHELL_ART not in result.output


def test_flag_overrides_environment(started: Path) -> None:
    # The fixture sets SHELLQUEST_MASCOT=1, and the explicit flag still wins.
    assert SHELL_ART not in run("--no-mascot", "mission").output


def test_silent_by_default_when_piped(home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SHELLQUEST_MASCOT", raising=False)
    run("start")

    assert SHELL_ART not in run("mission").output
    assert SHELL_ART not in run("check", "nutmeg").output
    assert SHELL_ART not in run("hint").output
