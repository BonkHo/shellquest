"""Finding things missions."""

from shellquest import checks
from shellquest.missions import CheckResult, Context, Mission

TOPIC = "Finding things"
INVOICES = "archive/2023/q4/invoices"


def _check_test_count(ctx: Context, answer: str) -> CheckResult:
    return CheckResult(checks.matches_number(answer, "4"))


def _check_race_file(ctx: Context, answer: str) -> CheckResult:
    return CheckResult(checks.matches_file(answer, "sync.py"))


def _check_todo_count(ctx: Context, answer: str) -> CheckResult:
    return CheckResult(checks.matches_number(answer, "6"))


def _check_invoices_cwd(ctx: Context, answer: str) -> CheckResult:
    # resolve() on both sides: macOS temp folders sit behind symlinks (/var -> /private/var),
    # and Path.cwd() already returns the resolved path.
    if ctx.cwd.resolve() == (ctx.root / INVOICES).resolve():
        return CheckResult(True)
    return CheckResult(False, "You're not in the invoices folder yet. Run check from inside it.")


def _check_code_word(ctx: Context, answer: str) -> CheckResult:
    # Piping the file in (`bat $(fzf) | shellquest check`) ends on "Code word: marmalade".
    word = checks.normalize(answer).removeprefix("code word:").strip()
    return CheckResult(checks.matches_text(word, "marmalade"))


FINDING = (
    Mission(
        id="find-1",
        topic=TOPIC,
        title="Test hunt",
        task="How many test files (named test_*.py) are there?",
        hints=(
            "`fd` finds files by name, searching every folder below where you are.",
            "`fd test` matches anything with 'test' in its name, including files that "
            "aren't tests. The pattern is a regex, so you can anchor it.",
            "Match names that start with `test_` and end in `.py`: `fd '^test_.*\\.py$'`. "
            "Then count the lines.",
        ),
        solution="fd '^test_.*\\.py$' | wc -l",
        explain=(
            "`fd` takes a regex: ^ anchors the start of the name, `.*` is anything, "
            "and `\\.` is a literal dot. `wc -l` counts the matches."
        ),
        kind="answer",
        check=_check_test_count,
        tools=("fd",),
    ),
    Mission(
        id="find-2",
        topic=TOPIC,
        title="Race condition",
        task="Which file has the FIXME about a race condition?",
        hints=(
            "`rg` (ripgrep) searches inside files, not just file names.",
            "Search for the words in the comment. Add `-l` to list only file names.",
            "`rg -l 'FIXME: race'`",
        ),
        solution="rg -l 'FIXME: race'",
        explain="`rg` searches file contents; `-l` prints just the names of matching files.",
        kind="answer",
        check=_check_race_file,
        tools=("rg",),
    ),
    Mission(
        id="find-3",
        topic=TOPIC,
        title="TODO count",
        task="How many TODO lines are in src/ ?",
        hints=(
            "`rg` prints one line per match, and you can tell it which folder to search.",
            "Searching is case-sensitive: `todo_list` is not a TODO. Limit the search to `src`.",
            "Pipe `rg TODO src` into `wc -l`.",
        ),
        solution="rg TODO src | wc -l",
        explain=(
            "`rg TODO src` prints each matching line in src/ only (not TODO.md), "
            "and `wc -l` counts them."
        ),
        kind="answer",
        check=_check_todo_count,
        tools=("rg",),
    ),
    Mission(
        id="find-4",
        topic=TOPIC,
        title="Jump around",
        task=(
            "`cd` into the invoices folder once, `cd ~`, then get back with `z invoices` "
            "and run check from there."
        ),
        hints=(
            "The invoices folder is deep inside archive/. Walk there once with `cd`, "
            "so zoxide learns it.",
            "`z` is zoxide's jump command: it remembers folders you've visited.",
            "After visiting the folder once and going back to `~`, run `z invoices`, "
            "then `shellquest check`.",
        ),
        solution="z invoices",
        explain="zoxide remembers folders you visit, so `z invoices` jumps there from anywhere.",
        kind="state",
        check=_check_invoices_cwd,
    ),
    Mission(
        id="find-5",
        topic=TOPIC,
        title="Fuzzy find",
        task=(
            'A file with "vault" in its name holds a code word. '
            "Pick it with fzf and read it with bat."
        ),
        hints=(
            "`fzf` is an interactive fuzzy finder: type part of a name and pick a match.",
            "fzf prints the file you picked, so `$(fzf)` can hand it to another command.",
            "Run `bat $(fzf)`, type `vault`, and press Enter.",
        ),
        solution="bat $(fzf)",
        # fzf is interactive, so the test uses its non-interactive --filter mode instead.
        reference='cat "$(find . -type f | fzf --filter vault)"',
        explain="`$(...)` runs fzf first and puts the file you picked into the bat command.",
        kind="answer",
        check=_check_code_word,
        tools=("fzf",),
    ),
)
