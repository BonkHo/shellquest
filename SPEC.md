# shellquest — spec

Terminal missions that teach the command line. `shellquest start` builds a throwaway practice folder (the **playground**) full of fake project files, then gives challenges. You solve each one in your real shell with real tools (fd, rg, jq, git, …), and `shellquest check` verifies the result before unlocking the next mission.

## How a session feels

```text
$ shellquest start
Playground ready at ~/shellquest-playground
→ cd ~/shellquest-playground

Mission basics-2 · Count the logs                     Shell basics 2/4
How many files ending in .log are in logs/ ?
Check with:  shellquest check <answer>   (or pipe into it)

$ ls logs/*.log | wc -l | shellquest check
✓ Correct: 7
  Another way:  fd -e log . logs | wc -l
  Why it works: the glob *.log expands before ls runs; wc -l counts lines.
Next: basics-3 · Make an index
```

## Commands

| Command | Does |
| --- | --- |
| `shellquest start` | Create the playground if missing, print the `cd` line and the current mission |
| `shellquest mission` | Show the current mission again |
| `shellquest check [ANSWER]` | Verify the current mission. Answer missions take ANSWER as an argument, from stdin when piped, or by prompting. State missions inspect the playground (and the current working directory) |
| `shellquest hint` | Reveal the next of up to 3 progressive hints |
| `shellquest list` | All missions by topic: ✓ done, ▶ current, · not started |
| `shellquest goto <id>` | Make another mission current |
| `shellquest reset [--yes] [--progress]` | Rebuild the playground; `--progress` also clears progress. Asks for confirmation unless `--yes` |

`shellquest check` must work from any folder, so the tool is installed with `uv tool install --editable .` (edits in the repo apply immediately).

## Mascot

Shelly the seashell is a small ASCII drawing with a speech bubble. She speaks **after** a command's normal output, never changing it:
- when a mission is shown (`start`, `mission`, `goto`), after a correct answer, after "Not quite", and after `hint`.
- she only says fixed phrases, so she never reveals an answer, and she saves nothing to `progress.json`.
- on by default only when output is a terminal, so piped output stays clean. `SHELLQUEST_MASCOT=1|0` or `shellquest --mascot|--no-mascot <command>` overrides that (the flag goes before the command and beats the environment variable).

## Paths and state

- Playground root: `$SHELLQUEST_HOME`, default `~/shellquest-playground`.
- Tool state lives in `$SHELLQUEST_HOME/.shellquest/`: a `marker` file and `progress.json` (current mission id, completed ids, hints used per mission).
- `reset` rebuilds everything except `.shellquest/` (unless `--progress`).
- **Safety:** never delete a folder unless it contains `.shellquest/marker`.

## Playground contents (fixture facts)

The builder is deterministic: every fact below must hold exactly, because missions depend on them. Tests assert each fact.

```text
~/shellquest-playground/
├── .shellquest/                 tool state (marker, progress.json)
├── .secret-ingredient           hidden; contains "saffron"
├── README.md                    short story: "You just joined the Pantry team…"
├── TODO.md                      distractor for TODO counting (outside src/)
├── scripts/backup.sh            mode 644 (not executable); bash script that prints
│                                BACKUP-OK-7731 via printf 'BACKUP-OK-%d\n' $((7700 + 31))
├── logs/                        exactly 7 files app-01.log … app-07.log
│                                + distractors app.log.gz and README.txt
│                                app-07.log last line: "shutdown complete: 312 orders processed"
├── notes/                       exactly 5 .md files: groceries.md, ideas.md,
│                                meeting-2024-03.md, recipes-to-try.md, test-plan.md
├── src/pantry/                  ~10 small .py files
│   ├── recipes.py               line 42 is exactly: def scale_recipe(recipe, servings):
│   ├── sync.py                  contains "# FIXME: race condition when two devices sync"
│   └── contest.py               distractor for fd
│                                Across src/: exactly 6 lines containing uppercase "TODO",
│                                plus lowercase distractors like todo_list
├── tests/                       exactly 4 files matching ^test_.*\.py$:
│   ├── test_recipes.py, test_pantry.py, test_sync.py
│   ├── integration/test_orders.py
│   └── testing_utils.py         distractor
├── data/
│   ├── orders.json              array of 40 orders {id, customer, status, amount};
│   │                            exactly 5 have status "refunded", amounts
│   │                            12.50, 25.00, 40.00, 47.50, 62.50 (total 187.50)
│   ├── inventory.csv            most lines, but small in bytes
│   └── photos.bin               largest file in data/ (~2 MB)
├── archive/2023/q4/invoices/    deep folder; several invoices +
│   └── inv-2023-12-vault.txt    contains "Code word: marmalade"
└── kitchen-api/                 its own git repo, branch main
```

### kitchen-api git repo

Files `app.py`, `routes.py`, `config.toml`. Six commits with fixed author names, emails (`@example.com`) and dates (set `GIT_AUTHOR_DATE` and `GIT_COMMITTER_DATE`), made with `git -c commit.gpgsign=false` so the builder never prompts for a signing key:

1. Sam Rivera: Initial commit
2. Alex Chen: Add routes for pantry items
3. Sam Rivera: hotfix: handle empty pantry
4. Alex Chen: Add config file
5. Sam Rivera: Refactor app startup
6. Sam Rivera: Raise request timeout to 45 seconds (`timeout = 30` → `timeout = 45` in config.toml)

After the last commit, `routes.py` has an uncommitted change.

## Missions

Two kinds:
- **answer**: the player submits a value.
- **state**: the tool inspects the playground or the current working directory.

Each mission has: `id`, `topic`, `title`, `task` (one or two sentences), `hints` (up to 3, progressively more specific), `solution` (the reference command), `explain` (one or two plain-language lines shown after success), and a `check` function.

### Shell basics
| id | Title | Task | Kind / answer | Reference solution |
| --- | --- | --- | --- | --- |
| basics-1 | Hidden in plain sight | A hidden file at the playground root names an ingredient. Which? | answer: `saffron` | `ls -A` then `cat .secret-ingredient` |
| basics-2 | Count the logs | How many `.log` files are in `logs/`? | answer: `7` | `ls logs/*.log \| wc -l` |
| basics-3 | Make an index | Save the names of every note in `notes/` into `notes/index.txt`. | state: file lists all 5 `.md` names (with or without `notes/` prefix) | `ls notes/*.md > notes/index.txt` |
| basics-4 | Permission denied | Run `scripts/backup.sh` and enter the code it prints. | answer: `BACKUP-OK-7731` **and** the file is executable | `chmod +x scripts/backup.sh && ./scripts/backup.sh` |

### Finding things
| id | Title | Task | Kind / answer | Reference solution |
| --- | --- | --- | --- | --- |
| find-1 | Test hunt | How many test files (named `test_*.py`) are there? | answer: `4` | `fd '^test_.*\.py$' \| wc -l` |
| find-2 | Race condition | Which file has the FIXME about a race condition? | answer: `sync.py` (basename or path) | `rg -l 'FIXME: race'` |
| find-3 | TODO count | How many TODO lines are in `src/`? | answer: `6` | `rg TODO src \| wc -l` |
| find-4 | Jump around | `cd` into the invoices folder once, `cd ~`, then get back with `z invoices` and run check from there. | state: cwd is `archive/2023/q4/invoices` | `z invoices` |
| find-5 | Fuzzy find | A file with "vault" in its name holds a code word. Pick it with fzf and read it with bat. | answer: `marmalade` | `bat $(fzf)` |

### Reading files and data
| id | Title | Task | Kind / answer | Reference solution |
| --- | --- | --- | --- | --- |
| read-1 | Last words | How many orders did the app process before the final shutdown in `logs/app-07.log`? | answer: `312` | `tail -n 1 logs/app-07.log` |
| read-2 | Line 42 | Which function is defined on line 42 of `src/pantry/recipes.py`? | answer: `scale_recipe` | `bat -r 42:42 src/pantry/recipes.py` |
| read-3 | Heavyweight | Which file in `data/` is the largest? | answer: `photos.bin` | `eza -l --sort=size data` |
| read-4 | Refund count | How many orders in `data/orders.json` were refunded? | answer: `5` | `jq '[.[] \| select(.status == "refunded")] \| length' data/orders.json` |
| read-5 | Refund total | What's the total refunded amount? | answer: `187.5` (accept 187.50, $187.50) | `jq '[.[] \| select(.status == "refunded") \| .amount] \| add' data/orders.json` |

### Git on the CLI (inside `kitchen-api/`)
| id | Title | Task | Kind / answer | Reference solution |
| --- | --- | --- | --- | --- |
| git-1 | Uncommitted | Which file has uncommitted changes? | answer: `routes.py` | `git status --short` |
| git-2 | Top committer | How many commits did Sam make? | answer: `4` | `git shortlog -sn HEAD` (without HEAD, shortlog waits on stdin when piped) |
| git-3 | What changed | What did the latest commit set the timeout to? | answer: `45` | `git show HEAD` (rendered by delta) |
| git-4 | Branch out | Create branch `add-greeting`, add `greeting.txt`, commit it. | state: branch exists, ahead of main, its tip contains `greeting.txt` | `git switch -c add-greeting && … && git commit` |

## Answer checking rules

- Input source: argument, else stdin if not a TTY, else an interactive prompt.
- Use the **last non-empty line** of the input (so `ls -A && cat …` piped in still works).
- Normalize: strip whitespace (macOS `wc -l` pads with spaces), surrounding quotes, and case.
- Numbers compare numerically; `$` and trailing zeros are ignored.
- File answers accept the basename or any path ending in it.
- On success: ✓, the reference solution as "Another way", the `explain` text, mark done, show next mission.
- On failure: "Not quite", and suggest `shellquest hint`. Never reveal the answer.

## Project layout

```text
src/shellquest/
  cli.py            Typer app and commands
  playground.py     builds the playground (pure functions, takes a root path)
  progress.py       load/save progress.json
  checks.py         answer normalization helpers
  mascot.py         Shelly the seashell: fixed phrases, ASCII art, on/off rules
  missions/
    __init__.py     Mission dataclass, registry, ordering
    basics.py  finding.py  reading.py  git.py
tests/
  conftest.py       fixture: SHELLQUEST_HOME → tmp_path, built playground
  test_playground.py   asserts every fixture fact above
  test_checks.py
  test_progress.py
  test_mascot.py
  test_missions.py     parametrized over all missions: the right answer passes,
                       a wrong answer fails; runs the reference command when its
                       tool is installed (skip otherwise)
  test_cli.py          Typer CliRunner smoke tests
```

## Tech

Python 3.12+, uv, Typer, Rich, pytest, Ruff. No other runtime dependencies.

## Out of scope for v1

GitHub (`gh`) missions (need network and auth), scores and streaks, a history coach that suggests better tools from `~/.zsh_history` (good v2), shell completion.
