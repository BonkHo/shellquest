from pathlib import Path

import pytest

from shellquest import progress
from shellquest.playground import PROGRESS


def test_missing_file_starts_at_first_mission(tmp_path: Path) -> None:
    assert progress.load(tmp_path, "basics-1") == progress.Progress(current="basics-1")


def test_round_trip(tmp_path: Path) -> None:
    saved = progress.Progress(
        current="basics-3", completed=["basics-1", "basics-2"], hints_used={"basics-2": 2}
    )

    progress.save(tmp_path, saved)

    assert progress.load(tmp_path, "basics-1") == saved


def test_save_leaves_no_temp_file(tmp_path: Path) -> None:
    progress.save(tmp_path, progress.Progress(current="basics-1"))

    assert [p.name for p in (tmp_path / ".shellquest").iterdir()] == ["progress.json"]


@pytest.mark.parametrize(
    "text", ["", "{not json", "[]", '{"completed": []}', '{"current": 1, "hints_used": 3}']
)
def test_unreadable_file_raises_with_a_way_out(tmp_path: Path, text: str) -> None:
    path = tmp_path / PROGRESS
    path.parent.mkdir()
    path.write_text(text)

    with pytest.raises(progress.ProgressError, match="reset --progress"):
        progress.load(tmp_path, "basics-1")
    assert path.read_text() == text  # never overwritten behind the player's back
