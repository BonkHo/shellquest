"""Every fixture fact from SPEC.md "Playground contents".

Values are written out here on purpose instead of imported from playground.py,
so a mistake in the builder can't silently agree with itself.
"""

import gzip
import json
import re
import stat
import subprocess
from pathlib import Path

import pytest

from shellquest.playground import PlaygroundError, build, reset


def _files(root: Path) -> list[Path]:
    return [p for p in root.rglob("*") if p.is_file()]


def _snapshot(root: Path) -> dict[str, tuple[bytes, int]]:
    return {
        str(p.relative_to(root)): (p.read_bytes(), stat.S_IMODE(p.stat().st_mode))
        for p in _files(root)
    }


# --- root ---


def test_marker_exists(playground: Path) -> None:
    assert (playground / ".shellquest" / "marker").is_file()


def test_secret_ingredient(playground: Path) -> None:
    assert (playground / ".secret-ingredient").read_text().strip() == "saffron"


def test_readme_and_todo(playground: Path) -> None:
    assert "You just joined the Pantry team" in (playground / "README.md").read_text()
    assert "TODO" in (playground / "TODO.md").read_text()


# --- scripts ---


def test_backup_script_is_not_executable(playground: Path) -> None:
    script = playground / "scripts" / "backup.sh"
    assert stat.S_IMODE(script.stat().st_mode) == 0o644


def test_backup_script_prints_code(playground: Path) -> None:
    script = playground / "scripts" / "backup.sh"
    assert "printf 'BACKUP-OK-%d\\n' $((7700 + 31))" in script.read_text()
    result = subprocess.run(["bash", str(script)], capture_output=True, text=True, check=True)
    assert result.stdout == "BACKUP-OK-7731\n"


# --- logs ---


def test_exactly_seven_log_files(playground: Path) -> None:
    names = sorted(p.name for p in (playground / "logs").glob("*.log"))
    assert names == [f"app-0{n}.log" for n in range(1, 8)]


def test_log_distractors(playground: Path) -> None:
    logs = playground / "logs"
    assert (logs / "README.txt").is_file()
    assert gzip.decompress((logs / "app.log.gz").read_bytes())


def test_last_log_line(playground: Path) -> None:
    last = (playground / "logs" / "app-07.log").read_text().splitlines()[-1]
    assert last.endswith("shutdown complete: 312 orders processed")


# --- notes ---


def test_exactly_five_notes(playground: Path) -> None:
    names = sorted(p.name for p in (playground / "notes").glob("*.md"))
    assert names == [
        "groceries.md",
        "ideas.md",
        "meeting-2024-03.md",
        "recipes-to-try.md",
        "test-plan.md",
    ]


# --- src ---


def test_recipes_line_42(playground: Path) -> None:
    lines = (playground / "src" / "pantry" / "recipes.py").read_text().splitlines()
    assert lines[41] == "def scale_recipe(recipe, servings):"


def test_sync_fixme(playground: Path) -> None:
    text = (playground / "src" / "pantry" / "sync.py").read_text()
    assert "# FIXME: race condition when two devices sync" in text


def test_fixme_race_only_in_sync(playground: Path) -> None:
    hits = [p.name for p in _files(playground) if b"FIXME: race" in p.read_bytes()]
    assert hits == ["sync.py"]


def test_contest_distractor(playground: Path) -> None:
    assert (playground / "src" / "pantry" / "contest.py").is_file()


def test_about_ten_python_files(playground: Path) -> None:
    assert 8 <= len(list((playground / "src" / "pantry").glob("*.py"))) <= 12


def test_exactly_six_todo_lines_in_src(playground: Path) -> None:
    lines = [line for p in _files(playground / "src") for line in p.read_text().splitlines()]
    assert sum("TODO" in line for line in lines) == 6
    assert any("todo_list" in line for line in lines)


def test_todo_md_is_outside_src(playground: Path) -> None:
    assert (playground / "TODO.md").is_file()
    assert not list((playground / "src").rglob("TODO*"))


# --- tests ---


def test_exactly_four_test_files(playground: Path) -> None:
    pattern = re.compile(r"^test_.*\.py$")
    matches = sorted(
        str(p.relative_to(playground)) for p in _files(playground) if pattern.match(p.name)
    )
    assert matches == [
        "tests/integration/test_orders.py",
        "tests/test_pantry.py",
        "tests/test_recipes.py",
        "tests/test_sync.py",
    ]
    assert (playground / "tests" / "testing_utils.py").is_file()


# --- data ---


def test_orders(playground: Path) -> None:
    orders = json.loads((playground / "data" / "orders.json").read_text())
    assert len(orders) == 40
    assert all(set(order) == {"id", "customer", "status", "amount"} for order in orders)
    assert len({order["id"] for order in orders}) == 40
    refunds = sorted(order["amount"] for order in orders if order["status"] == "refunded")
    assert refunds == [12.5, 25.0, 40.0, 47.5, 62.5]
    assert sum(refunds) == 187.5


def test_photos_is_largest(playground: Path) -> None:
    data = list((playground / "data").iterdir())
    largest = max(data, key=lambda p: p.stat().st_size)
    assert largest.name == "photos.bin"
    assert 1_900_000 < largest.stat().st_size < 2_200_000


def test_inventory_has_most_lines_but_fewest_bytes(playground: Path) -> None:
    data = list((playground / "data").iterdir())
    most_lines = max(data, key=lambda p: p.read_bytes().count(b"\n"))
    fewest_bytes = min(data, key=lambda p: p.stat().st_size)
    assert most_lines.name == "inventory.csv"
    assert fewest_bytes.name == "inventory.csv"


# --- archive ---


def test_vault_invoice(playground: Path) -> None:
    invoices = playground / "archive" / "2023" / "q4" / "invoices"
    assert "Code word: marmalade" in (invoices / "inv-2023-12-vault.txt").read_text()
    assert len(list(invoices.glob("inv-*.txt"))) >= 3


def test_only_one_vault_file(playground: Path) -> None:
    assert [p.name for p in _files(playground) if "vault" in p.name] == ["inv-2023-12-vault.txt"]


# --- determinism ---


def test_build_is_deterministic(tmp_path: Path) -> None:
    build(tmp_path / "a")
    build(tmp_path / "b")
    assert _snapshot(tmp_path / "a") == _snapshot(tmp_path / "b")


# --- safety and reset ---


def test_build_refuses_folder_without_marker(tmp_path: Path) -> None:
    (tmp_path / "keep.txt").write_text("mine")
    with pytest.raises(PlaygroundError):
        build(tmp_path)
    assert not (tmp_path / ".shellquest").exists()


def test_reset_refuses_folder_without_marker(tmp_path: Path) -> None:
    (tmp_path / "keep.txt").write_text("mine")
    with pytest.raises(PlaygroundError):
        reset(tmp_path)
    assert (tmp_path / "keep.txt").read_text() == "mine"


def test_reset_builds_missing_folder(home: Path) -> None:
    reset(home)
    assert (home / ".secret-ingredient").is_file()


def test_reset_restores_playground(playground: Path) -> None:
    before = _snapshot(playground)
    (playground / "logs" / "app-03.log").unlink()
    (playground / "notes" / "index.txt").write_text("stray")
    (playground / "scripts" / "backup.sh").chmod(0o755)
    reset(playground)
    assert _snapshot(playground) == before


def test_reset_keeps_progress(playground: Path) -> None:
    progress = playground / ".shellquest" / "progress.json"
    progress.write_text("{}")
    reset(playground)
    assert progress.read_text() == "{}"


def test_reset_clear_progress(playground: Path) -> None:
    progress = playground / ".shellquest" / "progress.json"
    progress.write_text("{}")
    reset(playground, clear_progress=True)
    assert not progress.exists()
    assert (playground / ".shellquest" / "marker").is_file()


def test_reset_does_not_follow_symlinks(playground: Path, tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "precious.txt").write_text("keep me")
    (playground / "link").symlink_to(outside, target_is_directory=True)
    reset(playground)
    assert not (playground / "link").exists()
    assert (outside / "precious.txt").read_text() == "keep me"
