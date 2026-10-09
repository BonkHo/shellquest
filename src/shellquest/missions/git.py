"""Git on the CLI missions (all inside the kitchen-api/ repo)."""

import os
import re
import subprocess

from shellquest import checks
from shellquest.missions import CheckResult, Context, Mission

TOPIC = "Git on the CLI"
REPO = "kitchen-api"
BRANCH = "add-greeting"

_MODIFIED_LINE = re.compile(r"^\s*modified:\s+(\S+)\s*$", re.MULTILINE)
_COMMIT_COUNT_LINE = re.compile(r"^\s*(\d+)\s+(.*sam.*)$", re.IGNORECASE | re.MULTILINE)
_TIMEOUT_VALUE = re.compile(r"\btimeout\s*(?:=|to)\s*(\d+)")


def _check_changed_file(ctx: Context, answer: str) -> CheckResult:
    # `git status --short` prints " M routes.py" (the status letters come first), and the long
    # `git status` lists "modified:   routes.py" in the middle of its output, not on the last line.
    if "routes.py" in _MODIFIED_LINE.findall(answer):
        return CheckResult(True)
    words = checks.normalize(answer).split()
    return CheckResult(bool(words) and checks.matches_file(words[-1], "routes.py"))


def _check_sam_commits(ctx: Context, answer: str) -> CheckResult:
    # `git shortlog -sn` sorts by count, so Sam's line isn't the last one: look for it anywhere.
    # A bare number (from `git log --author=Sam --oneline | wc -l`) is compared as usual.
    found = _COMMIT_COUNT_LINE.search(answer)
    ok = checks.matches_number(found.group(1) if found else answer, "4")
    return CheckResult(ok, shown=" ".join(found.group(0).split()) if found else None)


def _check_timeout(ctx: Context, answer: str) -> CheckResult:
    # The last line of `git show HEAD` is "+timeout = 45"; a commit message says "timeout to 45".
    line = checks.normalize(answer)
    found = _TIMEOUT_VALUE.search(line)
    return CheckResult(checks.matches_number(found.group(1) if found else line, "45"))


def _git(repo: str, *args: str) -> subprocess.CompletedProcess[str]:
    # Drop GIT_* variables (a leaked GIT_DIR would aim git at another repo).
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    return subprocess.run(
        ["git", "-C", repo, *args], env=env, capture_output=True, text=True, timeout=30
    )


def _check_greeting_branch(ctx: Context, answer: str) -> CheckResult:
    repo = str(ctx.root / REPO)
    try:
        if _git(repo, "rev-parse", "--verify", "--quiet", f"refs/heads/{BRANCH}").returncode:
            return CheckResult(False, f"There's no branch called {BRANCH} yet.")
        ahead = _git(repo, "rev-list", "--count", f"main..{BRANCH}")
        if ahead.returncode:
            return CheckResult(False, "The main branch is missing. Run `shellquest reset`.")
        if int(ahead.stdout) == 0:
            return CheckResult(False, f"{BRANCH} exists but has no commit of its own yet.")
        if _git(repo, "cat-file", "-e", f"{BRANCH}:greeting.txt").returncode:
            return CheckResult(
                False,
                f"The latest commit on {BRANCH} doesn't contain greeting.txt. "
                "Is the file created, added and committed?",
            )
    except (FileNotFoundError, subprocess.TimeoutExpired) as err:
        return CheckResult(False, f"Couldn't run git: {err}")
    return CheckResult(True)


GIT = (
    Mission(
        id="git-1",
        topic=TOPIC,
        title="Uncommitted",
        task="Inside kitchen-api/, which file has uncommitted changes?",
        hints=(
            "kitchen-api/ is its own git repo. `cd` into it first.",
            "`git status` shows what changed since the last commit.",
            "`git status --short` prints one line per changed file.",
        ),
        solution="git status --short",
        reference=f"cd {REPO} && git status --short",
        explain="`git status --short` lists changed files, one per line; ` M` means modified.",
        kind="answer",
        check=_check_changed_file,
        tools=("git",),
    ),
    Mission(
        id="git-2",
        topic=TOPIC,
        title="Top committer",
        task="Inside kitchen-api/, how many commits did Sam make?",
        hints=(
            "`git log` lists the commits, and each one names its author.",
            "`git shortlog` groups commits by author. `-s` shows only counts, `-n` sorts by count.",
            "Run `git shortlog -sn HEAD`. Without `HEAD` it waits for input when piped.",
        ),
        solution="git shortlog -sn HEAD",
        reference=f"cd {REPO} && git shortlog -sn HEAD",
        explain="`git shortlog -sn HEAD` counts commits per author, most commits first.",
        kind="answer",
        check=_check_sam_commits,
        tools=("git",),
    ),
    Mission(
        id="git-3",
        topic=TOPIC,
        title="What changed",
        task="Inside kitchen-api/, what did the latest commit set the timeout to?",
        hints=(
            "The latest commit is called HEAD.",
            "`git show` displays a commit: its message and the lines it changed.",
            "Run `git show HEAD`. Lines starting with `-` were removed and `+` were added.",
        ),
        solution="git show HEAD",
        reference=f"cd {REPO} && git show HEAD",
        explain=(
            "`git show HEAD` prints the latest commit and its diff: "
            "`-` lines are the old value, `+` lines the new one."
        ),
        kind="answer",
        check=_check_timeout,
        tools=("git",),
    ),
    Mission(
        id="git-4",
        topic=TOPIC,
        title="Branch out",
        task=(
            f"Inside kitchen-api/, create a branch called {BRANCH}, add a file greeting.txt "
            "to it and commit it."
        ),
        hints=(
            "`git switch -c <name>` creates a branch and moves onto it.",
            "Create the file (any text), then `git add greeting.txt` to stage it.",
            "Finish with `git commit -m 'your message'`, then run `shellquest check`.",
        ),
        solution=(
            f"git switch -c {BRANCH} && echo hello > greeting.txt "
            "&& git add greeting.txt && git commit -m 'Add greeting'"
        ),
        # Tests run with a temporary HOME, so there is no git identity or signing setup.
        reference=(
            f"cd {REPO} && git switch -c {BRANCH} && echo hello > greeting.txt "
            "&& git add greeting.txt && git -c user.name=Tester -c user.email=tester@example.com "
            "-c commit.gpgsign=false commit -m 'Add greeting'"
        ),
        explain=(
            "A branch is a separate line of commits. `git add` stages a file, "
            "and `git commit` saves the staged files onto the current branch."
        ),
        kind="state",
        check=_check_greeting_branch,
        tools=("git",),
    ),
)
