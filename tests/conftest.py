import os
import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest

from shellquest.playground import build


@pytest.fixture
def home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point SHELLQUEST_HOME at a temp folder so tests never touch the real home folder."""
    root = tmp_path / "playground"
    monkeypatch.setenv("SHELLQUEST_HOME", str(root))
    return root


@pytest.fixture
def playground(home: Path) -> Path:
    """A freshly built playground."""
    build(home)
    return home


@pytest.fixture
def run_git() -> Callable[..., str]:
    """run_git(root, *args): run git inside the playground's kitchen-api repo, as a test player.

    Fixed identity and no global config, so a developer's signing setup can't interfere.
    """

    def run(root: Path, *args: str) -> str:
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        env |= {
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_AUTHOR_NAME": "Tester",
            "GIT_AUTHOR_EMAIL": "tester@example.com",
            "GIT_COMMITTER_NAME": "Tester",
            "GIT_COMMITTER_EMAIL": "tester@example.com",
        }
        done = subprocess.run(
            ["git", "-c", "commit.gpgsign=false", *args],
            cwd=root / "kitchen-api",
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        return done.stdout

    return run
