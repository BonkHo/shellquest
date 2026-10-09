"""Every fixture fact from SPEC.md "Playground contents".

Values are written out here on purpose instead of imported from playground.py,
so a mistake in the builder can't silently agree with itself.
"""

import gzip
import json
import os
import re
import stat
import subprocess
from pathlib import Path

import pytest

from shellquest.playground import PlaygroundError, build, reset


def _files(root: Path) -> list[Path]:
    # .git/ is skipped: its index stores file timestamps, so it differs between identical builds.
    # The repo's content is checked through git itself (see the kitchen-api section).
    return [p for p in root.rglob("*") if p.is_file() and ".git" not in p.relative_to(root).parts]


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


# --- kitchen-api git repo ---

COMMITS = [  # oldest first: (author, subject, date)
    ("Sam Rivera", "Initial commit", "2024-02-12T09:30:00Z"),
    ("Alex Chen", "Add routes for pantry items", "2024-02-15T14:05:00Z"),
    ("Sam Rivera", "hotfix: handle empty pantry", "2024-02-19T11:20:00Z"),
    ("Alex Chen", "Add config file", "2024-02-26T16:45:00Z"),
    ("Sam Rivera", "Refactor app startup", "2024-03-04T10:10:00Z"),
    ("Sam Rivera", "Raise request timeout to 45 seconds", "2024-03-06T15:00:00Z"),
]


def _git_out(repo: Path, *args: str) -> str:
    """Run a read-only git command in a built repo, ignoring the developer's git config."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env |= {"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}
    done = subprocess.run(
        ["git", *args], cwd=repo, env=env, capture_output=True, text=True, check=True
    )
    return done.stdout


@pytest.fixture
def repo(playground: Path) -> Path:
    return playground / "kitchen-api"


def test_kitchen_api_is_a_repo_on_main(repo: Path) -> None:
    assert _git_out(repo, "rev-parse", "--show-toplevel").strip() == str(repo.resolve())
    assert _git_out(repo, "branch", "--show-current").strip() == "main"
    assert _git_out(repo, "branch", "--format=%(refname:short)").split() == ["main"]
    assert _git_out(repo, "stash", "list") == ""


def test_kitchen_api_files(repo: Path) -> None:
    tracked = sorted(_git_out(repo, "ls-files").split())
    assert tracked == ["app.py", "config.toml", "routes.py"]


def test_kitchen_api_has_six_commits_in_order(repo: Path) -> None:
    log = _git_out(repo, "log", "--reverse", "--format=%an|%s|%aI").splitlines()
    assert [tuple(line.split("|")) for line in log] == COMMITS


def test_kitchen_api_authors_use_example_emails(repo: Path) -> None:
    emails = _git_out(repo, "log", "--format=%ae|%ce").split()
    assert len(emails) == 6
    assert all(pair.split("|")[0].endswith("@example.com") for pair in emails)


def test_kitchen_api_committer_matches_author(repo: Path) -> None:
    fields = _git_out(repo, "log", "--format=%an|%ae|%aI|%cn|%ce|%cI").splitlines()
    for line in fields:
        name, email, date, c_name, c_email, c_date = line.split("|")
        assert (name, email, date) == (c_name, c_email, c_date)


def test_kitchen_api_commits_are_unsigned(repo: Path) -> None:
    assert set(_git_out(repo, "log", "--format=%G?").split()) == {"N"}


def test_sam_made_four_commits_and_alex_two(repo: Path) -> None:
    names = _git_out(repo, "log", "--format=%an").splitlines()
    assert (names.count("Sam Rivera"), names.count("Alex Chen")) == (4, 2)


def test_last_commit_raises_the_timeout(repo: Path) -> None:
    assert _git_out(repo, "show", "--name-only", "--format=", "HEAD").split() == ["config.toml"]
    diff = _git_out(repo, "show", "--format=", "-U0", "HEAD").splitlines()
    assert [line for line in diff if line[0] in "+-" and line[:3] not in ("+++", "---")] == [
        "-timeout = 30",
        "+timeout = 45",
    ]
    assert (repo / "config.toml").read_text().splitlines()[-1] == "timeout = 45"


def test_only_routes_has_an_uncommitted_change(repo: Path) -> None:
    assert _git_out(repo, "status", "--porcelain") == " M routes.py\n"


def test_kitchen_api_has_no_distractor_strings(repo: Path) -> None:
    # Other missions search the whole playground, so the repo must not add accidental matches.
    text = "".join(p.read_text() for p in _files(repo))
    assert "TODO" not in text
    assert "FIXME" not in text


def test_kitchen_api_head_is_deterministic(tmp_path: Path) -> None:
    build(tmp_path / "a")
    build(tmp_path / "b")
    head = [_git_out(tmp_path / x / "kitchen-api", "rev-parse", "HEAD") for x in "ab"]
    assert head[0] == head[1]


def test_build_ignores_the_developers_git_setup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    build(tmp_path / "clean")
    # A hostile setup: signing on with a missing key, a hook that always fails, and a stray
    # GIT_DIR like the one git sets while running a hook.
    home = tmp_path / "home"
    hooks = home / "hooks"
    hooks.mkdir(parents=True)
    hook = hooks / "pre-commit"
    hook.write_text("#!/bin/sh\nexit 1\n")
    hook.chmod(0o755)
    (home / ".gitconfig").write_text(
        f"[commit]\n\tgpgsign = true\n[gpg]\n\tformat = ssh\n"
        f"[user]\n\tsigningkey = {home}/missing-key.pub\n[core]\n\thooksPath = {hooks}\n"
    )
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("GIT_DIR", str(tmp_path / "somewhere-else"))

    build(tmp_path / "hostile")

    heads = [
        _git_out(tmp_path / x / "kitchen-api", "rev-parse", "HEAD") for x in ("clean", "hostile")
    ]
    assert heads[0] == heads[1]


def test_reset_rebuilds_the_repo(playground: Path, repo: Path) -> None:
    head = _git_out(repo, "rev-parse", "HEAD")
    _git_out(repo, "switch", "-c", "scratch")
    (repo / "extra.txt").write_text("x")
    _git_out(repo, "add", "extra.txt")
    _git_out(
        repo,
        "-c", "user.name=T", "-c", "user.email=t@example.com", "-c", "commit.gpgsign=false",
        "commit", "-m", "extra",
    )  # fmt: skip

    reset(playground)

    assert _git_out(repo, "rev-parse", "HEAD") == head
    assert _git_out(repo, "branch", "--format=%(refname:short)").split() == ["main"]
    assert _git_out(repo, "status", "--porcelain") == " M routes.py\n"
