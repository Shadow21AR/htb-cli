"""
Dashboard commands.

Commands:
- htb dashboard favorites    - Show favorite/owned items
- htb dashboard inprogress   - Show in-progress items
- htb dashboard recommended  - Show recommended items
"""

from typing import Optional

import typer

from ..client import HTBError, api_get
from ..formatters import (
    console,
    create_table,
    print_error,
    print_json,
    print_key_value,
    sanitize_text,
)

app = typer.Typer(help="Dashboard overview")

_SECTION_LABELS = {
    "startingPoints": "Starting Point",
    "machines": "Machines",
    "challenges": "Challenges",
    "sherlocks": "Sherlocks",
    "proLabs": "Pro Labs",
    "tracks": "Tracks",
    "fortresses": "Fortresses",
}


def _show_dashboard(data: dict, title: str):
    """Render dashboard data as per-section tables."""
    for key, label in _SECTION_LABELS.items():
        items = data.get(key, [])
        if not items:
            continue
        if key == "startingPoints":
            continue
        table = create_table(["ID", "Name", "Progress"], f"{title} — {label}")
        for item in items:
            progress = item.get("progress")
            if progress is not None:
                progress_str = f"{progress}%"
            else:
                tasks_done = item.get("tasksCompleted")
                tasks_total = item.get("tasksTotal")
                if tasks_done is not None and tasks_total:
                    progress_str = f"{tasks_done}/{tasks_total}"
                else:
                    progress_str = ""
            table.add_row(
                str(item.get("id", "?")),
                sanitize_text(item.get("name", "?")),
                progress_str,
            )
        console.print(table)
        console.print()


def _collect(data: dict) -> list:
    """Collect all items across sections into a flat list."""
    result = []
    for key in ("machines", "challenges", "sherlocks", "proLabs", "tracks", "fortresses"):
        for item in data.get(key, []):
            item["_section"] = key
            result.append(item)
    return result


@app.command("favorites")
def favorites(
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Show your favorite / owned items."""
    try:
        data = api_get("/v5/user/dashboard/favorites")
        if raw:
            print_json(data)
        else:
            items = _collect(data)
            if not items:
                console.print("[dim]No favorites yet[/dim]")
                return
            _show_dashboard(data, "Favorites")
    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("inprogress")
def inprogress(
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Show your in-progress items."""
    try:
        data = api_get("/v5/user/dashboard/inprogress")
        if raw:
            print_json(data)
        else:
            items = _collect(data)
            if not items:
                console.print("[dim]Nothing in progress[/dim]")
                return
            _show_dashboard(data, "In Progress")
    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("recommended")
def recommended(
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Show recommended items for you."""
    try:
        data = api_get("/v5/user/dashboard/recommended")
        if raw:
            print_json(data)
        else:
            items = _collect(data)
            if not items:
                console.print("[dim]No recommendations[/dim]")
                return
            _show_dashboard(data, "Recommended")
    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)
