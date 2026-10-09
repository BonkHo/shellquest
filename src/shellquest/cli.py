"""Typer app and commands."""

import sys
from pathlib import Path
from typing import Annotated, NoReturn

import typer
from rich.console import Console
from rich.table import Table
from rich.text import Text

from shellquest import checks, mascot, missions, playground, progress
from shellquest.missions import Context, Mission

app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    help="Terminal missions that teach the command line.",
)
console = Console()
# Set by the callback below on every run: True/False when the player chose, None for "automatic".
_mascot_setting: bool | None = None


@app.callback()
def main(
    mascot_on: Annotated[
        bool | None,
        typer.Option(
            "--mascot/--no-mascot",
            envvar="SHELLQUEST_MASCOT",
            help="Show or hide Shelly the seashell. Default: only in a terminal, not when piped.",
        ),
    ] = None,
) -> None:
    global _mascot_setting
    _mascot_setting = mascot_on


def _display(path: Path) -> str:
    """Show paths under the home folder as ~/..., like the shell does."""
    try:
        return f"~/{path.relative_to(Path.home())}"
    except ValueError:
        return str(path)


def _fail(message: str) -> NoReturn:
    console.print(message, style="red", markup=False, soft_wrap=True)
    raise typer.Exit(1)


def _print_ready(root: Path, status: str = "ready") -> None:
    # soft_wrap stops Rich from breaking long paths over two lines, so the cd line copies cleanly.
    console.print(f"Playground {status} at {_display(root)}", markup=False, soft_wrap=True)
    console.print(f"→ cd {_display(root)}", markup=False, soft_wrap=True)


def _require_playground() -> Path:
    root = playground.playground_home()
    if not playground.is_playground(root):
        _fail("No playground yet. Run `shellquest start`.")
    return root


def _load_progress(root: Path) -> progress.Progress:
    try:
        return progress.load(root, missions.all_missions()[0].id)
    except progress.ProgressError as err:
        _fail(str(err))


def _current(saved: progress.Progress) -> Mission:
    """The saved current mission, or the first unfinished one if that id no longer exists."""
    return (
        missions.get(saved.current)
        or missions.first_unfinished(saved.completed)
        or missions.all_missions()[0]
    )


def _say(mood: mascot.Mood, key: str) -> None:
    """Shelly always speaks last, after the lines the spec pins down, and never says an answer."""
    if mascot.is_enabled(_mascot_setting, console):
        mascot.say(console, mood, key)


def _show_mission(mission: Mission) -> None:
    in_topic = missions.in_topic(mission)
    header = Table.grid(expand=True)
    header.add_column()
    header.add_column(justify="right")
    header.add_row(
        Text(f"Mission {mission.id} · {mission.title}", style="bold"),
        Text(f"{mission.topic} {in_topic.index(mission) + 1}/{len(in_topic)}", style="dim"),
    )
    console.print()
    console.print(header)
    console.print(mission.task, markup=False)
    if mission.kind == "answer":
        how = "shellquest check <answer>   (or pipe into it)"
    else:
        how = "shellquest check"
    console.print(f"Check with:  {how}", markup=False, soft_wrap=True)
    _say("hello", mission.id)


def _stdin_is_tty() -> bool:
    return sys.stdin.isatty()


def _read_answer(argument: str | None) -> str:
    """The argument, else piped stdin, else a prompt (SPEC: Answer checking rules)."""
    if argument is not None:
        return argument
    if _stdin_is_tty():
        return typer.prompt("Your answer")
    try:
        return sys.stdin.read()
    except UnicodeDecodeError:  # e.g. someone piped a binary file in
        return ""


@app.command()
def start() -> None:
    """Create the playground if missing, print the cd line and the current mission."""
    root = playground.playground_home()
    if playground.is_playground(root):
        _print_ready(root, status="already")
    else:
        try:
            playground.build(root)
        except playground.PlaygroundError as err:
            _fail(f"{err} Set SHELLQUEST_HOME to use another folder.")
        _print_ready(root)
    _show_mission(_current(_load_progress(root)))


@app.command()
def mission() -> None:
    """Show the current mission again."""
    _show_mission(_current(_load_progress(_require_playground())))


@app.command()
def check(
    answer: Annotated[
        str | None, typer.Argument(help="Your answer. Read from stdin when piped.")
    ] = None,
) -> None:
    """Verify the current mission."""
    root = _require_playground()
    saved = _load_progress(root)
    current = _current(saved)
    # State missions look at files, so they never read input (a pipe left open would hang).
    given = _read_answer(answer) if current.kind == "answer" else ""
    try:
        cwd = Path.cwd()
    except FileNotFoundError:  # the shell's folder was deleted under it
        cwd = root
    result = current.check(Context(root=root, cwd=cwd), given)

    if not result.ok:
        console.print("Not quite.", style="red", markup=False)
        if result.note:
            console.print(result.note, markup=False)
        console.print("Try again, or run `shellquest hint`.", markup=False)
        _say("oops", f"{current.id}:{saved.hints_used.get(current.id, 0)}")
        raise typer.Exit(1)

    echoed = checks.last_line(given).strip() if result.shown is None else result.shown
    shown = f": {echoed}" if current.kind == "answer" else ""
    console.print(f"✓ Correct{shown}", style="green", markup=False, soft_wrap=True)
    console.print(f"  Another way:  {current.solution}", markup=False, soft_wrap=True)
    console.print(f"  Why it works: {current.explain}", markup=False)
    if current.id not in saved.completed:
        saved.completed.append(current.id)
    following = missions.next_after(current.id, saved.completed)
    if following:
        saved.current = following.id
    progress.save(root, saved)
    if following:
        console.print(f"Next: {following.id} · {following.title}", markup=False)
        _say("cheer", current.id)
    else:
        console.print("You've finished every mission available so far.", markup=False)
        _say("done", current.id)


@app.command()
def hint() -> None:
    """Reveal the next of up to 3 progressive hints."""
    root = _require_playground()
    saved = _load_progress(root)
    current = _current(saved)
    used = saved.hints_used.get(current.id, 0)
    out_of_hints = used >= len(current.hints)
    if not out_of_hints:
        saved.hints_used[current.id] = used = used + 1
        progress.save(root, saved)
    console.print(f"Hint {used}/{len(current.hints)}: {current.hints[used - 1]}", markup=False)
    if out_of_hints:
        console.print("That's all the hints for this mission.", style="dim", markup=False)
    _say("hint", f"{current.id}:{used}")


@app.command("list")
def list_missions() -> None:
    """All missions by topic: ✓ done, ▶ current, · not started."""
    saved = _load_progress(_require_playground())
    current = _current(saved)
    for topic in missions.topics():
        in_topic = [m for m in missions.all_missions() if m.topic == topic]
        done = sum(m.id in saved.completed for m in in_topic)
        console.print()
        console.print(Text(f"{topic}  {done}/{len(in_topic)}", style="bold"))
        for m in in_topic:
            if m.id == current.id:
                symbol, style = "▶", "yellow"
            elif m.id in saved.completed:
                symbol, style = "✓", "green"
            else:
                symbol, style = "·", "dim"
            console.print(Text(f"  {symbol} {m.id}  {m.title}", style=style))


@app.command()
def goto(
    mission_id: Annotated[str, typer.Argument(metavar="ID", help="Mission id, e.g. basics-2.")],
) -> None:
    """Make another mission current."""
    root = _require_playground()
    target = missions.get(mission_id)
    if target is None:
        _fail(f"No mission called {mission_id}. Run `shellquest list` to see them.")
    saved = _load_progress(root)
    saved.current = target.id
    progress.save(root, saved)
    _show_mission(target)


@app.command()
def reset(
    yes: Annotated[bool, typer.Option("--yes", help="Skip the confirmation prompt.")] = False,
    progress: Annotated[bool, typer.Option("--progress", help="Also clear progress.")] = False,
) -> None:
    """Rebuild the playground. Asks for confirmation unless --yes."""
    root = playground.playground_home()
    if not yes:
        lost = "your changes and progress" if progress else "your changes"
        typer.confirm(f"Rebuild {_display(root)}? All {lost} there will be lost.", abort=True)
    try:
        playground.reset(root, clear_progress=progress)
    except playground.PlaygroundError as err:
        _fail(str(err))
    _print_ready(root)
