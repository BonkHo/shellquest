import os
import shutil
import subprocess
from pathlib import Path

import pytest

from shellquest import missions
from shellquest.missions import CheckResult, Context, Mission

ALL = missions.all_missions()
IDS = [m.id for m in ALL]


def run_shell(script: str, cwd: Path, home: Path) -> str:
    """Run a script the way a player would in the playground; return its stdout."""
    # HOME points at a temp folder so a mission's command can never touch the real one.
    env = {**os.environ, "HOME": str(home)}
    done = subprocess.run(
        ["sh", "-c", script], cwd=cwd, env=env, capture_output=True, text=True, timeout=30
    )
    assert done.returncode == 0, done.stderr
    return done.stdout


def check(mission: Mission, root: Path, answer: str = "") -> CheckResult:
    return mission.check(Context(root=root, cwd=root), answer)


def mission_by_id(mission_id: str) -> Mission:
    found = missions.get(mission_id)
    assert found is not None
    return found


def test_ids_are_unique() -> None:
    assert len(set(IDS)) == len(IDS)


@pytest.mark.parametrize("mission", ALL, ids=IDS)
def test_mission_is_complete(mission: Mission) -> None:
    assert 1 <= len(mission.hints) <= 3
    for text in (mission.task, mission.solution, mission.explain, *mission.hints):
        assert text.strip()
    assert mission.kind in ("answer", "state")


@pytest.mark.parametrize("mission", ALL, ids=IDS)
def test_reference_solution_passes(mission: Mission, playground: Path, tmp_path: Path) -> None:
    for tool in mission.tools:
        if shutil.which(tool) is None:
            pytest.skip(f"{tool} is not installed")

    output = run_shell(mission.reference or mission.solution, playground, tmp_path)

    result = check(mission, playground, output if mission.kind == "answer" else "")
    assert result.ok, result.note


@pytest.mark.parametrize("mission", ALL, ids=IDS)
def test_wrong_answer_fails(mission: Mission, playground: Path) -> None:
    # Answer missions get a wrong answer; state missions are checked before anything is done.
    result = check(mission, playground, "not-the-answer" if mission.kind == "answer" else "")

    assert not result.ok


class TestBasics3:
    """The index must list all 5 notes; extras are only allowed if they are index.txt itself."""

    NAMES = ["groceries.md", "ideas.md", "meeting-2024-03.md", "recipes-to-try.md", "test-plan.md"]

    def write_index(self, root: Path, lines: list[str]) -> CheckResult:
        (root / "notes" / "index.txt").write_text("\n".join(lines) + "\n")
        return check(mission_by_id("basics-3"), root)

    def test_bare_names(self, playground: Path) -> None:
        assert self.write_index(playground, self.NAMES).ok

    def test_notes_prefix(self, playground: Path) -> None:
        assert self.write_index(playground, [f"notes/{n}" for n in self.NAMES]).ok

    def test_ls_of_the_whole_folder_also_lists_index_txt(self, playground: Path) -> None:
        assert self.write_index(playground, ["index.txt", *self.NAMES]).ok

    def test_missing_file(self, playground: Path) -> None:
        result = check(mission_by_id("basics-3"), playground)

        assert not result.ok
        assert "doesn't exist" in result.note

    def test_missing_one_note(self, playground: Path) -> None:
        assert not self.write_index(playground, self.NAMES[:-1]).ok

    def test_long_listing_is_not_a_list_of_names(self, playground: Path) -> None:
        long_listing = [f"-rw-r--r--  1 me  staff  120 Mar  1 notes/{n}" for n in self.NAMES]

        assert not self.write_index(playground, long_listing).ok

    def test_extra_file_name(self, playground: Path) -> None:
        assert not self.write_index(playground, [*self.NAMES, "secret.txt"]).ok


class TestBasics4:
    CODE = "BACKUP-OK-7731"

    def test_right_code_but_not_executable(self, playground: Path) -> None:
        result = check(mission_by_id("basics-4"), playground, self.CODE)

        assert not result.ok
        assert "executable" in result.note
        assert "7731" not in result.note  # a hint may nudge, but never gives the answer away

    def test_executable_but_wrong_code(self, playground: Path) -> None:
        (playground / "scripts" / "backup.sh").chmod(0o755)

        result = check(mission_by_id("basics-4"), playground, "BACKUP-OK-0000")

        assert not result.ok
        assert result.note == ""

    def test_both(self, playground: Path) -> None:
        (playground / "scripts" / "backup.sh").chmod(0o755)

        assert check(mission_by_id("basics-4"), playground, f"  {self.CODE}\n").ok

    def test_script_deleted(self, playground: Path) -> None:
        (playground / "scripts" / "backup.sh").unlink()

        result = check(mission_by_id("basics-4"), playground, self.CODE)

        assert not result.ok
        assert "reset" in result.note


def next_id(mission_id: str, completed: list[str]) -> str | None:
    following = missions.next_after(mission_id, completed)
    return following.id if following else None


class TestOrdering:
    def test_next_after_skips_finished_missions(self) -> None:
        assert next_id("basics-1", ["basics-1", "basics-2"]) == "basics-3"

    def test_next_after_wraps_to_earlier_missions(self) -> None:
        assert next_id("basics-4", ["basics-4", "basics-2"]) == "basics-1"

    def test_next_after_is_none_when_everything_is_done(self) -> None:
        assert next_id("basics-1", IDS) is None

    def test_topics_keep_play_order(self) -> None:
        assert missions.topics()[0] == "Shell basics"
