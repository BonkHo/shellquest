"""Shell basics missions."""

from shellquest import checks
from shellquest.missions import CheckResult, Context, Mission

TOPIC = "Shell basics"
NOTE_NAMES = (
    "groceries.md",
    "ideas.md",
    "meeting-2024-03.md",
    "recipes-to-try.md",
    "test-plan.md",
)


def _check_secret(ctx: Context, answer: str) -> CheckResult:
    return CheckResult(checks.matches_text(answer, "saffron"))


def _check_log_count(ctx: Context, answer: str) -> CheckResult:
    return CheckResult(checks.matches_number(answer, "7"))


def _check_index(ctx: Context, answer: str) -> CheckResult:
    index = ctx.root / "notes" / "index.txt"
    if not index.is_file():
        return CheckResult(False, "notes/index.txt doesn't exist yet.")
    # Each line is a bare name or has a notes/ prefix. Anything else (say `ls -l` output)
    # stays as it is, so it shows up below as an unexpected extra line.
    names = {
        line.strip().removeprefix("./").removeprefix("notes/")
        for line in index.read_text(errors="replace").splitlines()
        if line.strip()
    }
    names.discard("index.txt")  # `ls notes > notes/index.txt` lists the new file itself too
    missing = set(NOTE_NAMES) - names
    if missing:
        return CheckResult(False, f"notes/index.txt is missing {len(missing)} of the 5 notes.")
    if names - set(NOTE_NAMES):
        return CheckResult(False, "notes/index.txt lists more than just the note names.")
    return CheckResult(True)


def _check_backup(ctx: Context, answer: str) -> CheckResult:
    if not checks.matches_text(answer, "BACKUP-OK-7731"):
        return CheckResult(False)
    script = ctx.root / "scripts" / "backup.sh"
    if not script.is_file():
        return CheckResult(False, "scripts/backup.sh is missing. `shellquest reset` restores it.")
    if not script.stat().st_mode & 0o111:
        return CheckResult(False, "That's the right code, but scripts/backup.sh isn't executable.")
    return CheckResult(True)


BASICS = (
    Mission(
        id="basics-1",
        topic=TOPIC,
        title="Hidden in plain sight",
        task="A hidden file at the playground root names an ingredient. Which?",
        hints=(
            "Files whose names start with a dot are hidden from a plain `ls`.",
            "`ls -A` lists hidden files too.",
            "The hidden file's name starts with `.secret`. Print it with `cat`.",
        ),
        solution="ls -A, then cat .secret-ingredient",
        reference="ls -A && cat .secret-ingredient",
        explain="`ls -A` shows dotfiles that `ls` hides; `cat` prints a file's contents.",
        kind="answer",
        check=_check_secret,
    ),
    Mission(
        id="basics-2",
        topic=TOPIC,
        title="Count the logs",
        task="How many .log files are in logs/ ?",
        hints=(
            "`ls` can list just the files matching a pattern.",
            "`wc -l` counts lines, and `ls` prints one name per line when piped.",
            "Pipe `ls logs/*.log` into `wc -l`.",
        ),
        solution="ls logs/*.log | wc -l",
        explain="The glob *.log expands before ls runs; wc -l counts lines.",
        kind="answer",
        check=_check_log_count,
    ),
    Mission(
        id="basics-3",
        topic=TOPIC,
        title="Make an index",
        task="Save the names of every note in notes/ into notes/index.txt.",
        hints=(
            "`>` sends a command's output into a file instead of the screen.",
            "Notes are the .md files, so list them with a glob.",
            "`ls notes/*.md` lists them; add `> notes/index.txt` to save the list.",
        ),
        solution="ls notes/*.md > notes/index.txt",
        explain="`>` redirects output into a file, creating it or replacing what was there.",
        kind="state",
        check=_check_index,
    ),
    Mission(
        id="basics-4",
        topic=TOPIC,
        title="Permission denied",
        task="Run scripts/backup.sh and enter the code it prints.",
        hints=(
            "Try `./scripts/backup.sh`. The error tells you what's missing.",
            "A script needs the execute permission before you can run it directly.",
            "`chmod +x scripts/backup.sh` adds it. Then run the script again.",
        ),
        solution="chmod +x scripts/backup.sh && ./scripts/backup.sh",
        explain="`chmod +x` gives a file the execute permission, which running it directly needs.",
        kind="answer",
        check=_check_backup,
    ),
)
