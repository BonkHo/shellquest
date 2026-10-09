"""Typer app and commands."""

from pathlib import Path
from typing import Annotated, NoReturn

import typer
from rich.console import Console

from shellquest import playground

app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    help="Terminal missions that teach the command line.",
)
console = Console()


def _not_implemented() -> None:
    console.print("not implemented yet")


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


@app.command()
def start() -> None:
    """Create the playground if missing, print the cd line and the current mission."""
    root = playground.playground_home()
    if playground.is_playground(root):
        _print_ready(root, status="already")
        return
    try:
        playground.build(root)
    except playground.PlaygroundError as err:
        _fail(f"{err} Set SHELLQUEST_HOME to use another folder.")
    _print_ready(root)


@app.command()
def mission() -> None:
    """Show the current mission again."""
    _not_implemented()


@app.command()
def check(
    answer: Annotated[
        str | None, typer.Argument(help="Your answer. Read from stdin when piped.")
    ] = None,
) -> None:
    """Verify the current mission."""
    _not_implemented()


@app.command()
def hint() -> None:
    """Reveal the next of up to 3 progressive hints."""
    _not_implemented()


@app.command("list")
def list_missions() -> None:
    """All missions by topic: ✓ done, ▶ current, · not started."""
    _not_implemented()


@app.command()
def goto(
    mission_id: Annotated[str, typer.Argument(metavar="ID", help="Mission id, e.g. basics-2.")],
) -> None:
    """Make another mission current."""
    _not_implemented()


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
