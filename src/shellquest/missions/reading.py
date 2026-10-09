"""Reading files and data missions."""

import re

from shellquest import checks
from shellquest.missions import CheckResult, Context, Mission

TOPIC = "Reading files and data"

_SHUTDOWN_COUNT = re.compile(r"shutdown complete:\s*(\d+)")
_DEF_NAME = re.compile(r"\bdef\s+(\w+)")


def _check_orders_processed(ctx: Context, answer: str) -> CheckResult:
    # `tail -n 1` prints the whole log line; take the count out of it. A bare number also works.
    line = checks.normalize(answer)
    found = _SHUTDOWN_COUNT.search(line)
    return CheckResult(checks.matches_number(found.group(1) if found else line, "312"))


def _check_function_name(ctx: Context, answer: str) -> CheckResult:
    # `bat -r 42:42` prints the whole `def ...` line, maybe with a line number in front.
    line = checks.normalize(answer)
    found = _DEF_NAME.search(line)
    return CheckResult(checks.matches_text(found.group(1) if found else line, "scale_recipe"))


def _check_largest_file(ctx: Context, answer: str) -> CheckResult:
    # `eza -l` prints a table row with the name as its last word.
    words = checks.normalize(answer).split()
    return CheckResult(bool(words) and checks.matches_file(words[-1], "photos.bin"))


def _check_refund_count(ctx: Context, answer: str) -> CheckResult:
    return CheckResult(checks.matches_number(answer, "5"))


def _check_refund_total(ctx: Context, answer: str) -> CheckResult:
    return CheckResult(checks.matches_number(answer, "187.5"))


READING = (
    Mission(
        id="read-1",
        topic=TOPIC,
        title="Last words",
        task=("How many orders did the app process before the final shutdown in logs/app-07.log ?"),
        hints=(
            "The answer is on the last line of the file. You don't need to open the whole log.",
            "`tail` shows the end of a file. `-n 3` shows the last three lines.",
            "`tail -n 1 logs/app-07.log` prints just the last line. Read the number in it.",
        ),
        solution="tail -n 1 logs/app-07.log",
        explain="`tail -n 1` prints the last line of a file, so you skip the rest of the log.",
        kind="answer",
        check=_check_orders_processed,
    ),
    Mission(
        id="read-2",
        topic=TOPIC,
        title="Line 42",
        task="Which function is defined on line 42 of src/pantry/recipes.py ?",
        hints=(
            "You can print one line of a file instead of scrolling to it.",
            "`bat` can show part of a file with `-r` (short for `--line-range`), like `-r 5:9`.",
            "`bat -r 42:42 src/pantry/recipes.py` shows only line 42.",
        ),
        solution="bat -r 42:42 src/pantry/recipes.py",
        explain="`bat -r 42:42` shows the line range 42 to 42: just that one line, with colors.",
        kind="answer",
        check=_check_function_name,
        tools=("bat",),
    ),
    Mission(
        id="read-3",
        topic=TOPIC,
        title="Heavyweight",
        task="Which file in data/ is the largest?",
        hints=(
            "A long listing shows the size of each file.",
            "`eza -l` is a long listing, and `--sort=size` orders the rows by size.",
            "`eza -l --sort=size data` puts the smallest first, so the biggest is the last row.",
        ),
        solution="eza -l --sort=size data",
        explain="`eza -l` lists files with their sizes, and `--sort=size` puts the biggest last.",
        kind="answer",
        check=_check_largest_file,
        tools=("eza",),
    ),
    Mission(
        id="read-4",
        topic=TOPIC,
        title="Refund count",
        task="How many orders in data/orders.json were refunded?",
        hints=(
            "`jq` reads JSON. `jq '.[0]' data/orders.json` shows the first order.",
            "`.[]` goes through every order, and `select(...)` keeps only those that match a test. "
            "Wrap it all in `[ ]` to collect the matches into a list.",
            'Collect the refunded orders with `[.[] | select(.status == "refunded")]`, '
            "then pipe that into `length`.",
        ),
        solution="jq '[.[] | select(.status == \"refunded\")] | length' data/orders.json",
        explain=(
            "`.[]` visits every order, `select` keeps the refunded ones, "
            "and `length` counts the list."
        ),
        kind="answer",
        check=_check_refund_count,
        tools=("jq",),
    ),
    Mission(
        id="read-5",
        topic=TOPIC,
        title="Refund total",
        task="What's the total refunded amount?",
        hints=(
            "Start from your refund filter from the last mission.",
            "Instead of keeping the whole order, pull out one field with `| .amount`.",
            "Collect the amounts in a list, then pipe it into `add`.",
        ),
        solution="jq '[.[] | select(.status == \"refunded\") | .amount] | add' data/orders.json",
        explain="After `select`, `.amount` picks one field from each order and `add` sums them.",
        kind="answer",
        check=_check_refund_total,
        tools=("jq",),
    ),
)
