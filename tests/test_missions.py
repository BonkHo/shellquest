import os
import shutil
import subprocess
from pathlib import Path

import pytest

from shellquest import missions
from shellquest.missions import CheckResult, Context, Mission

ALL = missions.all_missions()
IDS = [m.id for m in ALL]

# Missions whose reference can't run in `sh -c`; each has its own test class instead.
NOT_RUNNABLE = {"find-4": "needs an interactive shell with zoxide"}


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
    if mission.id in NOT_RUNNABLE:
        pytest.skip(NOT_RUNNABLE[mission.id])
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


def needs(tool: str) -> None:
    if shutil.which(tool) is None:
        pytest.skip(f"{tool} is not installed")


class TestFind1:
    def test_unanchored_fd_gives_the_wrong_count(self, playground: Path, tmp_path: Path) -> None:
        needs("fd")
        output = run_shell("fd test | wc -l", playground, tmp_path)

        assert not check(mission_by_id("find-1"), playground, output).ok


class TestFind2:
    def test_path_is_accepted(self, playground: Path) -> None:
        assert check(mission_by_id("find-2"), playground, "src/pantry/sync.py").ok

    def test_distractor_file_is_not(self, playground: Path) -> None:
        assert not check(mission_by_id("find-2"), playground, "src/pantry/contest.py").ok


class TestFind3:
    def test_counting_the_whole_playground_is_wrong(self, playground: Path, tmp_path: Path) -> None:
        needs("rg")
        output = run_shell("rg TODO | wc -l", playground, tmp_path)  # also counts TODO.md

        assert not check(mission_by_id("find-3"), playground, output).ok


class TestFind5:
    @pytest.mark.parametrize("answer", ["marmalade", "Code word: marmalade", "'Marmalade'\n"])
    def test_accepts_the_word_or_the_whole_line(self, playground: Path, answer: str) -> None:
        assert check(mission_by_id("find-5"), playground, answer).ok

    def test_rejects_other_words(self, playground: Path) -> None:
        assert not check(mission_by_id("find-5"), playground, "Code word: saffron").ok


class TestFind4:
    INVOICES = Path("archive/2023/q4/invoices")

    def at(self, root: Path, cwd: Path) -> CheckResult:
        return mission_by_id("find-4").check(Context(root=root, cwd=cwd), "")

    def test_in_the_invoices_folder(self, playground: Path) -> None:
        assert self.at(playground, playground / self.INVOICES).ok

    @pytest.mark.parametrize(
        "elsewhere",
        [Path(), Path("archive/2023/q4"), Path("src"), Path("archive/2023/q4/invoices/..")],
    )
    def test_anywhere_else_fails(self, playground: Path, elsewhere: Path) -> None:
        result = self.at(playground, playground / elsewhere)

        assert not result.ok
        assert "archive" not in result.note  # a nudge, not the path

    def test_a_subfolder_of_invoices_fails(self, playground: Path) -> None:
        deeper = playground / self.INVOICES / "deeper"
        deeper.mkdir()

        assert not self.at(playground, deeper).ok

    def test_reached_through_a_symlink(self, playground: Path, tmp_path: Path) -> None:
        link = tmp_path / "shortcut"
        link.symlink_to(playground / self.INVOICES)

        assert self.at(playground, link).ok


class TestRead1:
    @pytest.mark.parametrize(
        "answer",
        [
            "312",
            "  312\n",
            "'312'",
            "2024-03-07 18:00:00 INFO shutdown complete: 312 orders processed",
        ],
    )
    def test_accepts_the_number_or_the_whole_line(self, playground: Path, answer: str) -> None:
        assert check(mission_by_id("read-1"), playground, answer).ok

    @pytest.mark.parametrize("day", [1, 6])
    def test_another_days_last_line_fails(self, playground: Path, day: int) -> None:
        log = (playground / "logs" / f"app-0{day}.log").read_text()

        assert not check(mission_by_id("read-1"), playground, log).ok

    def test_the_date_in_the_line_is_not_the_answer(self, playground: Path) -> None:
        line = "2024-03-07 18:00:00 INFO shutdown complete: 12 orders processed"

        assert not check(mission_by_id("read-1"), playground, line).ok


class TestRead2:
    @pytest.mark.parametrize(
        "answer",
        [
            "scale_recipe",
            "def scale_recipe(recipe, servings):",
            "  42 │ def scale_recipe(recipe, servings):",
        ],
    )
    def test_accepts_the_name_or_the_whole_line(self, playground: Path, answer: str) -> None:
        assert check(mission_by_id("read-2"), playground, answer).ok

    def test_another_function_in_the_file_fails(self, playground: Path) -> None:
        lines = (playground / "src" / "pantry" / "recipes.py").read_text().splitlines()
        other = next(
            line for line in lines if line.startswith("def ") and "scale_recipe" not in line
        )

        assert not check(mission_by_id("read-2"), playground, other).ok


class TestRead3:
    SIZES = {"photos.bin": "2.0Mi", "orders.json": "3.9k", "inventory.csv": "2.1k"}

    def row(self, name: str) -> str:
        return f".rw-r--r--  {self.SIZES[name]} me  9 Oct 07:11 {name}"

    @pytest.mark.parametrize("answer", ["photos.bin", "data/photos.bin"])
    def test_accepts_the_name_or_a_path(self, playground: Path, answer: str) -> None:
        assert check(mission_by_id("read-3"), playground, answer).ok

    def test_accepts_the_last_row_of_a_long_listing(self, playground: Path) -> None:
        assert check(mission_by_id("read-3"), playground, self.row("photos.bin")).ok

    @pytest.mark.parametrize("name", ["orders.json", "inventory.csv"])
    def test_other_files_fail(self, playground: Path, name: str) -> None:
        assert not check(mission_by_id("read-3"), playground, self.row(name)).ok

    def test_reversed_listing_ends_on_the_smallest_file(
        self, playground: Path, tmp_path: Path
    ) -> None:
        # Known limitation: the check reads the last line, so `--reverse` must be typed instead.
        needs("eza")
        output = run_shell("eza -l --sort=size --reverse data", playground, tmp_path)

        assert not check(mission_by_id("read-3"), playground, output).ok


class TestRead4:
    def test_counting_every_order_is_wrong(self, playground: Path, tmp_path: Path) -> None:
        needs("jq")
        output = run_shell("jq length data/orders.json", playground, tmp_path)  # 40 orders

        assert not check(mission_by_id("read-4"), playground, output).ok


class TestRead5:
    @pytest.mark.parametrize("answer", ["187.5", "187.50", "$187.50", "'187.5'\n"])
    def test_accepts_the_total_in_any_format(self, playground: Path, answer: str) -> None:
        assert check(mission_by_id("read-5"), playground, answer).ok

    def test_the_count_is_not_the_total(self, playground: Path) -> None:
        assert not check(mission_by_id("read-5"), playground, "5").ok

    def test_summing_every_order_is_wrong(self, playground: Path, tmp_path: Path) -> None:
        needs("jq")
        output = run_shell("jq '[.[] | .amount] | add' data/orders.json", playground, tmp_path)

        assert not check(mission_by_id("read-5"), playground, output).ok


def next_id(mission_id: str, completed: list[str]) -> str | None:
    following = missions.next_after(mission_id, completed)
    return following.id if following else None


class TestOrdering:
    def test_next_after_skips_finished_missions(self) -> None:
        assert next_id("basics-1", ["basics-1", "basics-2"]) == "basics-3"

    def test_next_after_wraps_to_earlier_missions(self) -> None:
        assert next_id("read-5", ["read-5", "basics-2"]) == "basics-1"

    def test_next_after_is_none_when_everything_is_done(self) -> None:
        assert next_id("basics-1", IDS) is None

    def test_topics_keep_play_order(self) -> None:
        assert missions.topics()[0] == "Shell basics"
