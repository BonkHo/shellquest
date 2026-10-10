"""Shelly, the seashell mascot: a small drawing with a speech bubble that reacts to the player."""

import textwrap
import zlib
from typing import Literal, get_args

from rich.console import Console

Mood = Literal["hello", "cheer", "oops", "hint", "done"]

# Fixed phrases only. Nothing here may ever include a mission's answer or solution.
LINES: dict[Mood, tuple[str, ...]] = {
    "hello": (
        "Hi, I'm Shelly! Stuck? Try `shellquest hint`.",
        "Ready when you are. I'll be right here!",
        "Take your time. There's no tide to beat.",
    ),
    "cheer": (
        "Shell yeah! You nailed it.",
        "Sea what you did there? Brilliant!",
        "Pearl-fectly done!",
    ),
    "oops": (
        "Hmm, not quite. Try `shellquest hint`?",
        "Close, maybe? Hints are free, no shame.",
        "Even great divers resurface. Try again!",
    ),
    "hint": (
        "Hope that helps! Give it another go.",
        "A little nudge from your shell friend.",
        "Does that wash something up?",
    ),
    "done": (
        "That's every mission. You're a shell master now!",
        "All done! I'm so proud I could crack.",
    ),
}

# Each mood gets its own face, so the shell looks happy, worried, and so on.
FACES: dict[Mood, str] = {
    "hello": "o_o",
    "cheer": "^o^",
    "oops": "o_O",
    "hint": "o.o",
    "done": "*o*",
}

BUBBLE_WIDTH = 48


def is_enabled(setting: bool | None, console: Console) -> bool:
    """False/True are explicit (flag or SHELLQUEST_MASCOT); None means only on a real terminal.

    Staying quiet when output is piped keeps scripts and `| cat` clean.
    """
    if setting is None:
        return console.is_terminal
    return setting


def line_for(mood: Mood, key: str) -> str:
    """Pick a phrase from a stable hash of `key`, so the same moment always gets the same words.

    Python's built-in hash() changes between runs, which is why this uses crc32.
    """
    pool = LINES[mood]
    return pool[zlib.crc32(key.encode()) % len(pool)]


def render(mood: Mood, key: str) -> list[str]:
    """The shell with a speech bubble beside it, as lines of plain text."""
    # Every row is 13 wide (an odd number), so the 3-character face sits exactly in the middle.
    shell = [
        r'   _.-"-._   ',
        r" .'\  |  /'. ",
        rf" \   {FACES[mood]}   / ",
        r"  `-.___.-'  ",
    ]
    words = textwrap.wrap(line_for(mood, key), BUBBLE_WIDTH)
    width = max(len(word) for word in words)
    bubble = [f" .{'-' * (width + 2)}."]
    for i, word in enumerate(words):
        edge = "<" if i == 0 else "|"  # the < points at the shell, like a speech bubble tail
        bubble.append(f"{edge}  {word.ljust(width)} |")
    bubble.append(f" '{'-' * (width + 2)}'")
    # Pad the shorter side so no row of the shell or the bubble gets cut off.
    rows = max(len(shell), len(bubble))
    shell += [" " * len(shell[0])] * (rows - len(shell))
    bubble += [""] * (rows - len(bubble))
    return [f"{art}{box}".rstrip() for art, box in zip(shell, bubble, strict=True)]


def say(console: Console, mood: Mood, key: str) -> None:
    console.print()
    for row in render(mood, key):
        console.print(row, style="magenta", markup=False, highlight=False, soft_wrap=True)


MOODS: tuple[Mood, ...] = get_args(Mood)
