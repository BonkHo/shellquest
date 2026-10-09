"""Load and save progress.json, which lives in the playground's .shellquest/ folder."""

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path

from shellquest.playground import PROGRESS


class ProgressError(Exception):
    """progress.json exists but can't be read."""


@dataclass
class Progress:
    current: str
    completed: list[str] = field(default_factory=list)
    hints_used: dict[str, int] = field(default_factory=dict)


def load(root: Path, first_mission: str) -> Progress:
    """Read progress, or start fresh at first_mission when there is none yet."""
    path = root / PROGRESS
    if not path.is_file():
        return Progress(current=first_mission)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return Progress(
            current=str(data["current"]),
            completed=[str(i) for i in data.get("completed", [])],
            hints_used={str(k): int(v) for k, v in data.get("hints_used", {}).items()},
        )
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as err:
        raise ProgressError(
            f"Can't read {path} ({err}). Run `shellquest reset --progress` to start over."
        ) from err


def save(root: Path, progress: Progress) -> None:
    """Write progress atomically: write a temp file, then rename it over the real one."""
    path = root / PROGRESS
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".json.tmp")
    temp.write_text(json.dumps(asdict(progress), indent=2) + "\n", encoding="utf-8")
    os.replace(temp, path)
