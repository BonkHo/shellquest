"""Build the practice folder (the playground). Pure functions that take a root path."""

import gzip
import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

STATE_DIR = ".shellquest"
MARKER = f"{STATE_DIR}/marker"
PROGRESS = f"{STATE_DIR}/progress.json"

FILE_MODE = 0o644
MARKER_TEXT = "Created by shellquest. `shellquest reset` may delete and rebuild this folder.\n"


class PlaygroundError(Exception):
    """The folder exists but is not a shellquest playground, so we refuse to touch it."""


def playground_home() -> Path:
    """The playground root: $SHELLQUEST_HOME, or ~/shellquest-playground."""
    env = os.environ.get("SHELLQUEST_HOME")
    if env:
        return Path(env).expanduser()
    return Path.home() / "shellquest-playground"


def is_playground(root: Path) -> bool:
    return (root / MARKER).is_file()


def build(root: Path) -> None:
    """Write every playground file under root. Refuses a non-empty folder without a marker."""
    if root.exists() and any(root.iterdir()) and not is_playground(root):
        raise PlaygroundError(f"{root} already exists and is not a shellquest playground.")
    # Marker first, so even a half-built folder can still be reset safely.
    _write(root / MARKER, MARKER_TEXT)
    for rel, content in _files().items():
        _write(root / rel, content)
    _build_kitchen_api(root / "kitchen-api")


def reset(root: Path, *, clear_progress: bool = False) -> None:
    """Delete everything in root except .shellquest/, then build again."""
    if root.exists():
        if not is_playground(root):
            raise PlaygroundError(
                f"{root} has no {MARKER}, so shellquest will not delete anything in it."
            )
        for child in root.iterdir():
            if child.name == STATE_DIR:
                continue
            # Unlink symlinks instead of following them, so nothing outside root is touched.
            if child.is_dir() and not child.is_symlink():
                shutil.rmtree(child)
            else:
                child.unlink()
        if clear_progress:
            (root / PROGRESS).unlink(missing_ok=True)
    build(root)


def _write(path: Path, content: str | bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content, encoding="utf-8")
    # Set the mode explicitly so it doesn't depend on the user's umask.
    os.chmod(path, FILE_MODE)


def _lines(*lines: str) -> str:
    return "\n".join(lines) + "\n"


def _files() -> dict[str, str | bytes]:
    return {
        ".secret-ingredient": "saffron\n",
        "README.md": _readme(),
        "TODO.md": _todo_md(),
        "scripts/backup.sh": _lines(
            "#!/usr/bin/env bash",
            "# Nightly backup of the pantry database.",
            "printf 'BACKUP-OK-%d\\n' $((7700 + 31))",
        ),
        **_logs(),
        **_notes(),
        **_src(),
        **_tests(),
        **_data(),
        **_archive(),
    }


def _readme() -> str:
    return _lines(
        "# Welcome to the Pantry team",
        "",
        "You just joined the Pantry team, a small crew building an app that tracks",
        "what's in the kitchen, syncs it between devices and takes grocery orders.",
        "",
        "Your laptop has a fresh checkout of everything: source code in src/, tests,",
        "logs from last week's launch, some data exports and a dusty archive.",
        "Nobody remembers where anything is. Time to find out with the command line.",
    )


def _todo_md() -> str:
    return _lines(
        "# Team TODO",
        "",
        "- TODO: write onboarding docs",
        "- TODO: rotate the backup key",
        "- TODO: order more saffron",
    )


def _logs() -> dict[str, str | bytes]:
    files: dict[str, str | bytes] = {}
    for day in range(1, 8):
        processed = 312 if day == 7 else 40 * day + 3
        lines = [
            f"2024-03-0{day} 08:00:00 INFO starting pantry-app v1.{day}",
            f"2024-03-0{day} 08:00:01 INFO connected to database",
        ]
        for hour in range(9, 18):
            lines.append(f"2024-03-0{day} {hour:02d}:15:00 INFO processed order batch {hour - 8}")
        if day % 2 == 1:
            lines.append(f"2024-03-0{day} 13:42:10 WARN sync retry for device kitchen-ipad")
        lines.append(
            f"2024-03-0{day} 18:00:00 INFO shutdown complete: {processed} orders processed"
        )
        files[f"logs/app-{day:02d}.log"] = _lines(*lines)
    old = _lines(
        "2024-02-29 08:00:00 INFO starting pantry-app v0.9",
        "2024-02-29 18:00:00 INFO shutdown complete: 12 orders processed",
    )
    # mtime=0 keeps the gzip header free of the current time, so builds are identical.
    files["logs/app.log.gz"] = gzip.compress(old.encode(), mtime=0)
    files["logs/README.txt"] = _lines(
        "One log file per day: app-01.log to app-07.log.",
        "Older logs are compressed (app.log.gz).",
    )
    return files


def _notes() -> dict[str, str | bytes]:
    return {
        "notes/groceries.md": _lines("# Groceries", "", "- flour", "- eggs", "- saffron"),
        "notes/ideas.md": _lines("# Ideas", "", "- Barcode scanner", "- Shared shopping lists"),
        "notes/meeting-2024-03.md": _lines(
            "# Meeting, March 2024", "", "- Launch went fine", "- Sync bug on two devices"
        ),
        "notes/recipes-to-try.md": _lines("# Recipes to try", "", "- Paella", "- Risotto"),
        "notes/test-plan.md": _lines(
            "# Test plan", "", "- Unit tests for recipes", "- Integration test for orders"
        ),
    }


def _recipes_py() -> str:
    return _lines(
        "# Recipe helpers for the Pantry app.",
        "",
        "from dataclasses import dataclass, field",
        "",
        "from pantry.units import convert",
        "",
        "",
        "@dataclass",
        "class Ingredient:",
        "    name: str",
        "    amount: float",
        "    unit: str",
        "",
        "",
        "@dataclass",
        "class Recipe:",
        "    title: str",
        "    servings: int",
        "    ingredients: list[Ingredient] = field(default_factory=list)",
        "    steps: list[str] = field(default_factory=list)",
        "",
        "",
        "def total_ingredients(recipe):",
        "    return len(recipe.ingredients)",
        "",
        "",
        "def find_ingredient(recipe, name):",
        "    for ingredient in recipe.ingredients:",
        "        if ingredient.name == name:",
        "            return ingredient",
        "    return None",
        "",
        "",
        "def to_metric(recipe):",
        "    # TODO: support imperial cups",
        "    for ingredient in recipe.ingredients:",
        "        ingredient.amount, ingredient.unit = convert(ingredient.amount, ingredient.unit)",
        "    return recipe",
        "",
        "",
        "# Scaling keeps the step text unchanged; only the amounts move.",
        "def scale_recipe(recipe, servings):",  # line 42
        "    factor = servings / recipe.servings",
        "    scaled = Recipe(recipe.title, servings, steps=list(recipe.steps))",
        "    for ingredient in recipe.ingredients:",
        "        scaled.ingredients.append(",
        "            Ingredient(ingredient.name, ingredient.amount * factor, ingredient.unit)",
        "        )",
        "    return scaled",
    )


def _src() -> dict[str, str | bytes]:
    # Exactly 6 lines in src/ contain uppercase TODO; lowercase "todo" lines are distractors.
    return {
        "src/pantry/__init__.py": _lines("# Pantry: track what's in the kitchen."),
        "src/pantry/recipes.py": _recipes_py(),
        "src/pantry/sync.py": _lines(
            "# Keep the pantry in sync between devices.",
            "",
            "",
            "def sync(local, remote):",
            "    # FIXME: race condition when two devices sync",
            "    merged = {**remote, **local}",
            "    # TODO: keep a sync log per device",
            "    return merged",
        ),
        "src/pantry/contest.py": _lines(
            "# Monthly recipe contest: votes and winners.",
            "",
            "",
            "def winner(votes):",
            "    return max(votes, key=votes.get)",
        ),
        "src/pantry/inventory.py": _lines(
            "# Count what's on the shelves.",
            "",
            "",
            "def add_item(stock, name, qty):",
            "    # TODO: reject negative quantities",
            "    stock[name] = stock.get(name, 0) + qty",
            "    return stock",
            "",
            "",
            "def low_stock(stock, limit=2):",
            "    # TODO: make the limit configurable per item",
            "    return [name for name, qty in stock.items() if qty <= limit]",
        ),
        "src/pantry/orders.py": _lines(
            "# Grocery orders.",
            "",
            "",
            "def order_total(order):",
            "    # TODO: apply discount codes",
            "    return sum(line['price'] * line['qty'] for line in order['lines'])",
        ),
        "src/pantry/models.py": _lines(
            "# Plain data models.",
            "",
            "from dataclasses import dataclass",
            "",
            "",
            "@dataclass",
            "class Item:",
            "    name: str",
            "    qty: int",
        ),
        "src/pantry/storage.py": _lines(
            "# Save and load the pantry as JSON.",
            "",
            "import json",
            "",
            "",
            "def save(path, stock):",
            "    # TODO: write to a temp file first, then rename",
            "    with open(path, 'w') as f:",
            "        json.dump(stock, f)",
        ),
        "src/pantry/units.py": _lines(
            "# Unit conversion.",
            "",
            "GRAMS_PER_OUNCE = 28.35",
            "",
            "",
            "def convert(amount, unit):",
            "    if unit == 'oz':",
            "        return amount * GRAMS_PER_OUNCE, 'g'",
            "    return amount, unit",
        ),
        "src/pantry/utils.py": _lines(
            "# Small helpers.",
            "",
            "",
            "def make_todo_list(items):",
            "    # todo items are shown in the app's shopping tab",
            "    todo_list = [f'- {item}' for item in items]",
            "    return '\\n'.join(todo_list)",
        ),
    }


def _tests() -> dict[str, str | bytes]:
    return {
        "tests/test_recipes.py": _lines(
            "from pantry.recipes import Recipe, scale_recipe",
            "",
            "",
            "def test_scale_recipe_keeps_title():",
            "    assert scale_recipe(Recipe('Soup', 2), 4).title == 'Soup'",
        ),
        "tests/test_pantry.py": _lines(
            "from pantry.inventory import add_item",
            "",
            "",
            "def test_add_item():",
            "    assert add_item({}, 'eggs', 6) == {'eggs': 6}",
        ),
        "tests/test_sync.py": _lines(
            "from pantry.sync import sync",
            "",
            "",
            "def test_local_wins():",
            "    assert sync({'eggs': 1}, {'eggs': 2}) == {'eggs': 1}",
        ),
        "tests/integration/test_orders.py": _lines(
            "from pantry.orders import order_total",
            "",
            "",
            "def test_order_total():",
            "    assert order_total({'lines': [{'price': 2, 'qty': 3}]}) == 6",
        ),
        "tests/testing_utils.py": _lines(
            "# Shared helpers for tests (not a test file itself).",
            "",
            "",
            "def make_stock():",
            "    return {'eggs': 6, 'flour': 1}",
        ),
    }


REFUNDS = {4: 12.5, 11: 25.0, 19: 40.0, 27: 47.5, 36: 62.5}
CUSTOMERS = ["Ana", "Ben", "Chloe", "Dev", "Emma", "Farid", "Grace", "Hiro"]
OTHER_STATUSES = ["delivered", "shipped", "delivered", "pending"]
INVENTORY_ITEMS = ["salt", "rice", "oats", "eggs", "milk", "tea", "flour", "sugar", "beans", "jam"]


def _orders() -> list[dict[str, object]]:
    orders: list[dict[str, object]] = []
    for order_id in range(1, 41):
        if order_id in REFUNDS:
            status, amount = "refunded", REFUNDS[order_id]
        else:
            # Multiples of 0.25 are exact in binary floating point, so no 0.1+0.2 surprises.
            status = OTHER_STATUSES[order_id % len(OTHER_STATUSES)]
            amount = 8 + (order_id * 7.25) % 60
        orders.append(
            {
                "id": order_id,
                "customer": CUSTOMERS[order_id % len(CUSTOMERS)],
                "status": status,
                "amount": amount,
            }
        )
    return orders


def _data() -> dict[str, str | bytes]:
    # Many short rows: the most lines in data/, but the fewest bytes.
    rows = [f"{INVENTORY_ITEMS[i % len(INVENTORY_ITEMS)]},{(i * 7) % 20}" for i in range(300)]
    # A repeating byte pattern with no newline byte (10), so `wc -l` reports 0 lines.
    pattern = bytes(b for b in range(256) if b != 10)
    size = 2 * 1024 * 1024
    photos = (pattern * (size // len(pattern) + 1))[:size]
    return {
        "data/orders.json": json.dumps(_orders(), indent=2) + "\n",
        "data/inventory.csv": _lines("item,qty", *rows),
        "data/photos.bin": photos,
    }


def _archive() -> dict[str, str | bytes]:
    folder = "archive/2023/q4/invoices"
    return {
        f"{folder}/inv-2023-10-014.txt": _lines("Invoice 2023-10-014", "Flour x20: 31.00"),
        f"{folder}/inv-2023-11-027.txt": _lines("Invoice 2023-11-027", "Eggs x60: 18.00"),
        f"{folder}/inv-2023-12-031.txt": _lines("Invoice 2023-12-031", "Saffron x2: 24.00"),
        f"{folder}/inv-2023-12-vault.txt": _lines(
            "Invoice 2023-12 (vault copy)", "Code word: marmalade"
        ),
    }


@dataclass(frozen=True)
class Commit:
    author: str
    email: str
    date: str  # ISO 8601, used as both the author and the committer date
    subject: str
    files: dict[str, str]  # whole new contents of every file this commit changes


SAM = ("Sam Rivera", "sam@example.com")
ALEX = ("Alex Chen", "alex@example.com")

_ROUTES_V1 = _lines(
    "# HTTP routes for the kitchen API.",
    "",
    "",
    "def list_items(pantry):",
    "    return [{'name': name, 'qty': qty} for name, qty in pantry.items()]",
    "",
    "",
    "def get_item(pantry, name):",
    "    return {'name': name, 'qty': pantry[name]}",
)
_ROUTES_V2 = _lines(
    "# HTTP routes for the kitchen API.",
    "",
    "",
    "def list_items(pantry):",
    "    if not pantry:",
    "        return []",
    "    return [{'name': name, 'qty': qty} for name, qty in pantry.items()]",
    "",
    "",
    "def get_item(pantry, name):",
    "    return {'name': name, 'qty': pantry[name]}",
)
_APP_V1 = _lines(
    "# Entry point of the kitchen API.",
    "",
    "",
    "def main():",
    "    print('kitchen-api starting')",
    "",
    "",
    "main()",
)
_APP_V2 = _lines(
    "# Entry point of the kitchen API.",
    "",
    "from routes import list_items",
    "",
    "",
    "def main():",
    "    print('kitchen-api starting')",
    "    print(list_items({}))",
    "",
    "",
    "main()",
)
_APP_V3 = _lines(
    "# Entry point of the kitchen API.",
    "",
    "import tomllib",
    "",
    "from routes import list_items",
    "",
    "",
    "def load_config(path='config.toml'):",
    "    with open(path, 'rb') as f:",
    "        return tomllib.load(f)",
    "",
    "",
    "def main():",
    "    config = load_config()",
    "    print('kitchen-api starting on port', config['server']['port'])",
    "    print(list_items({}))",
    "",
    "",
    "if __name__ == '__main__':",
    "    main()",
)
# The timeout is deliberately the last line, so `git show HEAD` ends on the changed value.
_CONFIG_V1 = _lines("[server]", "port = 8080", "", "[requests]", "timeout = 30")
_CONFIG_V2 = _lines("[server]", "port = 8080", "", "[requests]", "timeout = 45")

KITCHEN_API_COMMITS = (
    Commit(*SAM, "2024-02-12T09:30:00+0000", "Initial commit", {"app.py": _APP_V1}),
    Commit(
        *ALEX,
        "2024-02-15T14:05:00+0000",
        "Add routes for pantry items",
        {"routes.py": _ROUTES_V1, "app.py": _APP_V2},
    ),
    Commit(
        *SAM, "2024-02-19T11:20:00+0000", "hotfix: handle empty pantry", {"routes.py": _ROUTES_V2}
    ),
    Commit(*ALEX, "2024-02-26T16:45:00+0000", "Add config file", {"config.toml": _CONFIG_V1}),
    Commit(*SAM, "2024-03-04T10:10:00+0000", "Refactor app startup", {"app.py": _APP_V3}),
    Commit(
        *SAM,
        "2024-03-06T15:00:00+0000",
        "Raise request timeout to 45 seconds",
        {"config.toml": _CONFIG_V2},
    ),
)
# Written after the last commit and left uncommitted: git-1 asks which file it is.
ROUTES_UNCOMMITTED = _ROUTES_V2 + "# Note: add a route for items that expire soon.\n"


def _git(repo: Path, *args: str, commit: Commit | None = None) -> None:
    """Run git in repo, ignoring the player's own git setup and fixing who and when."""
    # Drop every GIT_* variable: a leaked GIT_DIR (e.g. from a git hook) would aim git elsewhere.
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    # No global or system config, so signing keys, hook paths and templates can't interfere.
    env |= {"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}
    if commit:
        env |= {
            "GIT_AUTHOR_NAME": commit.author,
            "GIT_AUTHOR_EMAIL": commit.email,
            "GIT_AUTHOR_DATE": commit.date,
            "GIT_COMMITTER_NAME": commit.author,
            "GIT_COMMITTER_EMAIL": commit.email,
            "GIT_COMMITTER_DATE": commit.date,
        }
    try:
        # commit.gpgsign=false so the builder never asks for a signing key.
        subprocess.run(
            ["git", "-c", "commit.gpgsign=false", *args],
            cwd=repo,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        raise PlaygroundError("kitchen-api needs git, but git is not installed.") from None
    except subprocess.CalledProcessError as err:
        raise PlaygroundError(f"kitchen-api: `git {args[0]}` failed: {err.stderr.strip()}") from err


def _build_kitchen_api(repo: Path) -> None:
    """Create the kitchen-api repo: six fixed commits, then one uncommitted change."""
    repo.mkdir(parents=True, exist_ok=True)
    # An empty template means no sample hooks, so the repo holds only what we put in it.
    _git(repo, "init", "--quiet", "--initial-branch=main", "--template=")
    for commit in KITCHEN_API_COMMITS:
        for name, content in commit.files.items():
            _write(repo / name, content)
        _git(repo, "add", "--all")
        _git(repo, "commit", "--quiet", "-m", commit.subject, commit=commit)
    _write(repo / "routes.py", ROUTES_UNCOMMITTED)
