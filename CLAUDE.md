# shellquest

Terminal missions that teach the command line. Python package managed with uv. The design is in SPEC.md and the build order is in ROADMAP.md; read both before planning.

## Commands
- Install deps: `uv sync`
- Run: `uv run shellquest <command>` (or `shellquest` after `uv tool install --editable .`)
- Tests: `uv run pytest`
- Format and lint: `uv run ruff format . && uv run ruff check --fix .`
- **Full check, run before saying a step is done:** `uv run ruff format --check . && uv run ruff check . && uv run pytest`

## Conventions
- Python 3.12+, type hints everywhere, dataclasses over loose dicts.
- Typer for the CLI, Rich for output. Ask before adding any other runtime dependency.
- Work only on the ROADMAP step you were asked for, and tick its box when it's done.
- Every mission has a reference solution and tests proving the right answer passes and a wrong one fails.
- Tests never touch the real home folder: point `SHELLQUEST_HOME` at `tmp_path`.
- Git commits made by the playground builder use `git -c commit.gpgsign=false` and fixed authors and dates. My global git config signs commits, which would prompt for a key in tests.
- Never delete a folder unless it contains `.shellquest/marker`.

## About me
I'm learning the CLI with this project. When you use a shell command or Python feature I might not know, explain it in one line.
