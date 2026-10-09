"""The Mission dataclass, the registry of all missions, and their ordering."""

from collections.abc import Callable, Collection
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Literal


@dataclass(frozen=True)
class Context:
    """What a check may look at: the playground, and the folder the player ran `check` from."""

    root: Path
    cwd: Path


@dataclass(frozen=True)
class CheckResult:
    ok: bool
    # An optional nudge on failure. Never put the answer in it.
    note: str = ""


@dataclass(frozen=True)
class Mission:
    id: str
    topic: str
    title: str
    task: str
    hints: tuple[str, ...]
    solution: str  # shown after success as "Another way"
    explain: str
    kind: Literal["answer", "state"]
    # Gets the player's raw input (always "" for state missions).
    check: Callable[[Context, str], CheckResult]
    # A runnable shell script, for tests, when `solution` is prose rather than one command.
    reference: str | None = None
    # Programs the reference needs; its test is skipped when one isn't installed.
    tools: tuple[str, ...] = ()


@cache
def all_missions() -> tuple[Mission, ...]:
    """Every mission in play order. Topic modules are imported here, not at the top of the
    file, because they import Mission from this module (a top-level import would be circular)."""
    from shellquest.missions import basics

    return (*basics.BASICS,)


def get(mission_id: str) -> Mission | None:
    return next((m for m in all_missions() if m.id == mission_id), None)


def in_topic(mission: Mission) -> tuple[Mission, ...]:
    return tuple(m for m in all_missions() if m.topic == mission.topic)


def topics() -> list[str]:
    """Topic names in play order."""
    return list(dict.fromkeys(m.topic for m in all_missions()))


def first_unfinished(completed: Collection[str]) -> Mission | None:
    return next((m for m in all_missions() if m.id not in completed), None)


def next_after(mission_id: str, completed: Collection[str]) -> Mission | None:
    """The next unfinished mission after this one, wrapping to earlier ones; None if all done."""
    missions = all_missions()
    start = next((i for i, m in enumerate(missions) if m.id == mission_id), -1)
    for mission in (*missions[start + 1 :], *missions[: start + 1]):
        if mission.id not in completed:
            return mission
    return None
