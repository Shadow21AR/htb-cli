"""
Sherlock (DFIR investigation) commands.

Commands:
- htb sherlock list      - List sherlocks
- htb sherlock info      - Get sherlock details
- htb sherlock tasks     - Show tasks/questions
- htb sherlock download  - Download sherlock files
- htb sherlock own       - Submit flag/answer
"""

from enum import Enum
from pathlib import Path
from typing import Optional

import typer

from ..client import HTBError, api_download_bytes, api_get, api_post
from ..formatters import (
    console,
    print_error,
    print_flag_result,
    print_json,
    print_sherlock,
    print_sherlocks,
    print_success,
    print_warning,
    sanitize_text,
)

app = typer.Typer(help="Sherlock (DFIR investigation) management")


class Difficulty(str, Enum):
    """Sherlock difficulty levels."""
    easy = "easy"
    medium = "medium"
    hard = "hard"
    insane = "insane"


def _find_sherlock_by_name(name: str) -> dict | None:
    """Find a sherlock by name (case-insensitive) across all pages."""
    try:
        name_lower = name.lower()
        page = 1
        while True:
            data = api_get("/sherlocks", {"per_page": 100, "page": page})
            for s in data.get("data", []):
                if s.get("name", "").lower() == name_lower:
                    return s
            meta = data.get("meta", {})
            if page >= meta.get("last_page", 1):
                break
            page += 1
        return None
    except HTBError:
        return None


def _resolve_sherlock_id(name_or_id: str) -> int:
    """Resolve sherlock name or ID to numeric ID."""
    if name_or_id.isdigit():
        return int(name_or_id)

    sherlock = _find_sherlock_by_name(name_or_id)
    if sherlock:
        return sherlock["id"]

    raise HTBError(f"Sherlock not found: {name_or_id}")


@app.command("list")
def list_sherlocks(
    difficulty: Optional[Difficulty] = typer.Option(None, "--difficulty", "-d", help="Filter by difficulty"),
    unsolved: bool = typer.Option(False, "--unsolved", "-u", help="Show only unsolved"),
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    per_page: int = typer.Option(20, "--per-page", "-n", help="Items per page"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """List available sherlocks."""
    try:
        data = api_get("/sherlocks", {"per_page": per_page, "page": page})

        if raw:
            print_json(data)
            return

        sherlocks = data.get("data", [])

        # Apply filters
        if difficulty:
            sherlocks = [s for s in sherlocks if s.get("difficulty", "").lower() == difficulty.value]

        if unsolved:
            sherlocks = [s for s in sherlocks if not s.get("is_owned")]

        print_sherlocks(sherlocks)

        # Show pagination info
        meta = data.get("meta", {})
        if meta:
            total = meta.get("total", "?")
            current = meta.get("current_page", page)
            last = meta.get("last_page", "?")
            console.print(f"\n[dim]Page {current}/{last} (Total: {total})[/dim]")

    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("info")
def info(
    name: str = typer.Argument(..., help="Sherlock name or ID"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Get detailed information about a sherlock."""
    try:
        sherlock_id = _resolve_sherlock_id(name)
        data = api_get(f"/sherlocks/{sherlock_id}")

        if raw:
            print_json(data)
        else:
            print_sherlock(data.get("data", data))

    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("download")
def download(
    name: str = typer.Argument(..., help="Sherlock name or ID"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path"),
):
    """Download sherlock investigation files."""
    try:
        sherlock_id = _resolve_sherlock_id(name)
        content = api_download_bytes(f"/sherlocks/{sherlock_id}/download_link")

        # Get sherlock name for filename if not specified
        if output is None:
            try:
                info_data = api_get(f"/sherlocks/{sherlock_id}")
                sherlock_name = info_data.get("data", {}).get("name", f"sherlock_{sherlock_id}")
            except Exception:
                sherlock_name = f"sherlock_{sherlock_id}"
            output = Path(f"{sherlock_name}.zip")

        output.write_bytes(content)
        print_success(f"Downloaded to: {output}")

    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("own")
def own(
    name: str = typer.Argument(..., help="Sherlock name or ID"),
    flag: str = typer.Argument(..., help="Flag/answer to submit"),
    task: int = typer.Option(1, "--task", "-t", help="Task number (sherlocks have multiple questions)"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Submit an answer for a sherlock task."""
    try:
        sherlock_id = _resolve_sherlock_id(name)

        # Get task list to resolve task number to task ID
        tasks_data = api_get(f"/sherlocks/{sherlock_id}/tasks")
        tasks_list = tasks_data.get("data", [])

        if not tasks_list:
            print_error("No tasks found for this sherlock")
            raise typer.Exit(1)

        if task < 1 or task > len(tasks_list):
            print_error(f"Task number must be between 1 and {len(tasks_list)}")
            raise typer.Exit(1)

        task_id = tasks_list[task - 1]["id"]

        data = api_post(f"/sherlocks/{sherlock_id}/tasks/{task_id}/flag", {
            "flag": flag,
        })

        if raw:
            print_json(data)
        else:
            print_flag_result(data)

    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("tasks")
def tasks(
    name: str = typer.Argument(..., help="Sherlock name or ID"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Show tasks/questions for a sherlock."""
    try:
        sherlock_id = _resolve_sherlock_id(name)
        data = api_get(f"/sherlocks/{sherlock_id}/tasks")

        if raw:
            print_json(data)
            return

        tasks_list = data.get("data", [])

        if not tasks_list:
            print_warning("No tasks found for this sherlock")
            return

        # Get sherlock name for display
        try:
            sherlock_data = api_get(f"/sherlocks/{sherlock_id}")
            sherlock_name = sherlock_data.get("data", {}).get("name", "Unknown")
        except HTBError:
            sherlock_name = str(sherlock_id)

        console.print(f"[bold cyan]Tasks for: {sanitize_text(sherlock_name)}[/bold cyan]\n")

        for i, task in enumerate(tasks_list, 1):
            solved = task.get("completed")
            status = "[green]✓[/green]" if solved else "[dim]○[/dim]"
            question = sanitize_text(task.get("description", task.get("title", f"Task {i}")))
            console.print(f"  {status} [bold]{i}.[/bold] {question}")

    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)
