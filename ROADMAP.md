# shellquest — roadmap

One step = one Claude Code session = one or more small commits. Tick the box when a step is done.

## The loop for every step

1. `/clear` (fresh context, one task per session)
2. **Shift+Tab** until Plan mode, then paste the step's prompt
3. Read the plan. Push back on anything unclear or outside the step
4. Approve and let it work
5. **You verify** (each step says how). Don't skip this; it's the habit
6. `git diff`, and ask "why?" about any line you don't understand
7. Commit and push (ask Claude to commit with the suggested message, or do it yourself)
8. If you had to correct Claude, add one line about it to `CLAUDE.md`

---

## [ ] 0. Repo setup (by hand)

Done in the terminal, not Claude Code. See the setup commands in the chat.

## [x] 1. Skeleton

**Prompt**
> Read CLAUDE.md, SPEC.md and ROADMAP.md. Plan step 1 only: initialize this repo as a uv package project named shellquest (Python 3.12+), add Typer and Rich, add pytest and Ruff as dev dependencies, configure Ruff in pyproject.toml, and create the Typer app with every command from the SPEC as a stub that prints "not implemented yet". Add one CliRunner test that `--help` lists all commands. Finish by running the full check from CLAUDE.md.

**You verify**
- `uv tool install --editable .` then `shellquest --help` from a different folder (try `cd ~`)
- `uv run pytest` passes

**Commit:** `Set up uv project, Typer CLI skeleton and tests`

## [x] 2. Playground builder

**Prompt**
> Plan step 2 of ROADMAP.md: implement playground.py to build everything in the SPEC's "Playground contents" section except kitchen-api/ (that comes in step 6). Wire up `start` and `reset`, including the marker-file safety rule. Write test_playground.py asserting every fixture fact. Explain any shell or Python concept I might not know in one line.

**You verify**
- `shellquest start`, then `cd ~/shellquest-playground && eza --tree -a`
- Spot-check two facts yourself, e.g. `ls logs/*.log | wc -l` and `sed -n 42p src/pantry/recipes.py`
- `shellquest reset` asks for confirmation

**Commit:** `Build deterministic playground with start and reset`

## [x] 3. Mission engine + Shell basics

**Prompt**
> Plan step 3 of ROADMAP.md: the Mission dataclass and registry, progress.py, checks.py with the SPEC's answer checking rules, and the `mission`, `check`, `hint`, `list` and `goto` commands. Add the four Shell basics missions. Tests: test_checks.py for normalization (including macOS `wc -l` padding and piped multi-line input) and parametrized test_missions.py as described in the SPEC.

**You verify**
- Play basics-1 to basics-4 yourself without looking at the code
- Try a wrong answer, `shellquest hint` three times, and `shellquest list`
- Pipe an answer in: `ls logs/*.log | wc -l | shellquest check`

**Commit:** `Add mission engine and shell basics missions`

## [ ] 4. Finding things

**Prompt**
> Plan step 4 of ROADMAP.md: add the five Finding things missions from the SPEC. find-4 checks the current working directory. Reference-command tests should skip cleanly if fd, rg or fzf is missing.

**You verify**
- Play find-1 to find-5. For find-4, really use `z`
- Notice how `fd test` gives the wrong count and why the anchored regex fixes it

**Commit:** `Add finding things missions (fd, rg, zoxide, fzf)`

## [ ] 5. Reading files and data

**Prompt**
> Plan step 5 of ROADMAP.md: add the five Reading files and data missions from the SPEC, with tests.

**You verify**
- Play read-1 to read-5. For the jq ones, build the filter up one piece at a time (`jq '.[0]'`, then `.[] | .status`, …)

**Commit:** `Add reading files and data missions (tail, bat, eza, jq)`

## [ ] 6. Git missions

**Prompt**
> Plan step 6 of ROADMAP.md: extend the playground builder with the kitchen-api git repo exactly as the SPEC describes (fixed authors and dates, commit.gpgsign=false, uncommitted change at the end), add its facts to test_playground.py, then add the four Git missions with tests.

**You verify**
- `shellquest reset`, then `cd kitchen-api && git log --oneline` shows six commits
- Play git-1 to git-4. Look at `git show HEAD` with delta

**Commit:** `Add kitchen-api repo and git missions`

## [ ] 7. Polish and release

**Prompt**
> Plan step 7 of ROADMAP.md: write a README (what it is, install with `uv tool install`, a short demo transcript, mission list without answers), add a GitHub Actions workflow on macos-latest that installs fd, ripgrep, jq, bat and eza with Homebrew and runs the full check, and review the codebase for anything inconsistent with the SPEC.

**You verify**
- `gh run watch` after pushing shows CI passing
- Read the README as if you'd never seen the project
- Play every mission once from a fresh `shellquest reset --progress`

**Commit:** `Add README and CI`, then `git tag v0.1.0 && git push --tags`

---

## Later ideas
- History coach: suggest `fd`/`rg`/`z` based on `~/.zsh_history`
- `gh` missions (issues, PRs) against a scratch repo
- Parallelize: build two topics at once in separate git worktrees
