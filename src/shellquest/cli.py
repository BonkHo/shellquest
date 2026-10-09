"""Typer app and commands."""

from typing import Annotated

import typer
from rich.console import Console

app = typer.Typer(
    no_args_is_help=True,
    add_completion=False,
    help="Terminal missions that teach the command line.",
)
console = Console()


def _not_implemented() -> None:
    console.print("not implemented yet")


@app.command()
def start() -> None:
    """Create the playground if missing, print the cd line and the current mission."""
    _not_implemented()


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
    _not_implemented()
