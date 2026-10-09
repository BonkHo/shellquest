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
