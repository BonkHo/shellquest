# shellquest

Terminal missions that teach the command line.

`shellquest start` builds a throwaway practice folder (the **playground**) full of fake project
files from an imaginary kitchen-app team. Then it gives you challenges: find the hidden file, count
the TODOs, work out who committed what. You solve each one in your own shell with real tools
(`ls`, `fd`, `rg`, `jq`, `git`, …), and `shellquest check` verifies the result before unlocking the
next mission. Shelly the seashell cheers you on.

## Requirements

- [uv](https://docs.astral.sh/uv/) (it also fetches Python 3.12+ for you) and `git`
- The tools the missions use, via Homebrew:

  ```sh
  brew install fd ripgrep jq bat eza fzf zoxide git-delta
  ```

  shellquest itself runs without them, but each mission needs its tool. `zoxide` also needs
  `eval "$(zoxide init zsh)"` in your `~/.zshrc` so that `z` works. `delta` only makes `git show`
  prettier.

## Install

```sh
uv tool install git+https://github.com/BonkHo/shellquest
```

Or, if you want to change the code (edits apply immediately):

```sh
git clone https://github.com/BonkHo/shellquest.git
cd shellquest
uv tool install --editable .
```

Then `shellquest --help` works from any folder.

## A taste

```text
$ shellquest start
Playground ready at ~/shellquest-playground
→ cd ~/shellquest-playground

Mission basics-1 · Hidden in plain sight                        Shell basics 1/4
A hidden file at the playground root names an ingredient. Which?
Check with:  shellquest check <answer>   (or pipe into it)

$ cd ~/shellquest-playground
$ shellquest goto basics-2

Mission basics-2 · Count the logs                               Shell basics 2/4
How many .log files are in logs/ ?
Check with:  shellquest check <answer>   (or pipe into it)

$ shellquest check 9
Not quite.
Try again, or run `shellquest hint`.

$ shellquest hint
Hint 1/3: `ls` can list just the files matching a pattern.

$ ls logs/*.log | wc -l | shellquest check
✓ Correct: 7
  Another way:  ls logs/*.log | wc -l
  Why it works: The glob *.log expands before ls runs; wc -l counts lines.
Next: basics-3 · Make an index
```

(In a real terminal Shelly appears under each message. She is hidden when output is piped.)

## Commands

| Command | Does |
| --- | --- |
| `shellquest start` | Create the playground if missing, print the `cd` line and the current mission |
| `shellquest mission` | Show the current mission again |
| `shellquest check [ANSWER]` | Verify the current mission. Give the answer as an argument, pipe it in, or get prompted. Some missions check your files or your current folder instead |
| `shellquest hint` | Reveal the next of up to 3 progressive hints |
| `shellquest list` | All missions by topic: ✓ done, ▶ current, · not started |
| `shellquest goto <id>` | Make another mission current |
| `shellquest reset [--yes] [--progress]` | Rebuild the playground; `--progress` also clears your progress. Asks first unless `--yes` |

Settings:

- `SHELLQUEST_HOME`: where the playground lives (default `~/shellquest-playground`).
- `SHELLQUEST_MASCOT=0|1`, or `shellquest --no-mascot|--mascot <command>`: turn Shelly off or on.
  By default she only shows up in a terminal.

## Missions

Answers are not listed here, on purpose.

**Shell basics**: `ls`, `cat`, redirection, permissions

- `basics-1` Hidden in plain sight
- `basics-2` Count the logs
- `basics-3` Make an index
- `basics-4` Permission denied

**Finding things**: `fd`, `rg`, `zoxide`, `fzf`

- `find-1` Test hunt
- `find-2` Race condition
- `find-3` TODO count
- `find-4` Jump around
- `find-5` Fuzzy find

**Reading files and data**: `tail`, `bat`, `eza`, `jq`

- `read-1` Last words
- `read-2` Line 42
- `read-3` Heavyweight
- `read-4` Refund count
- `read-5` Refund total

**Git on the CLI**: `git status`, `shortlog`, `show`, `switch`, `commit`

- `git-1` Uncommitted
- `git-2` Top committer
- `git-3` What changed
- `git-4` Branch out

## Is it safe?

The playground is a normal folder you can poke at. shellquest only ever deletes a folder that
contains `.shellquest/marker`, the file it creates when it builds one. Anything else it refuses to
touch. Your progress lives in `.shellquest/progress.json` inside the playground.

## Development

```sh
uv sync
uv run ruff format --check . && uv run ruff check . && uv run pytest
```

The design is in [SPEC.md](SPEC.md) and the build order in [ROADMAP.md](ROADMAP.md). Tests never
touch your real home folder (they set `SHELLQUEST_HOME` to a temp folder), and a mission's
reference-command test is skipped when its tool isn't installed. CI runs the same check on macOS
with the tools above.

## License

MIT, see [LICENSE](LICENSE).
