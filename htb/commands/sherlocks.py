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
from ..files import resolve_output_path
from ..formatters import (
    console,
    print_error,
    print_flag_result,
    print_flag_submission_error,
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
    very_easy = "very-easy"
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
        params: dict = {"per_page": per_page, "page": page}
        if difficulty:
            params["difficulty[]"] = [difficulty.value]

        data = api_get("/sherlocks", params)

        if raw:
            print_json(data)
            return

        sherlocks = data.get("data", [])

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

        from rich.progress import BarColumn, DownloadColumn, Progress, TextColumn, TimeRemainingColumn, TransferSpeedColumn

        progress = Progress(
            TextColumn("[bold blue]Downloading…[/bold blue]"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
        )

        def _update(done, total):
            progress.update(task_id, completed=done, total=total or None)

        with progress:
            task_id = progress.add_task("", total=None)
            content = api_download_bytes(
                f"/sherlocks/{sherlock_id}/download_link",
                progress_callback=_update,
            )

        # Get sherlock name for filename
        try:
            info_data = api_get(f"/sherlocks/{sherlock_id}")
            sherlock_name = info_data.get("data", {}).get("name", f"sherlock_{sherlock_id}")
        except Exception:
            sherlock_name = f"sherlock_{sherlock_id}"

        filename = f"{sherlock_name}.zip"
        path = resolve_output_path(output, filename)
        path.write_bytes(content)
        print_success(f"Downloaded to: {path}")

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
        if print_flag_submission_error(e):
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
            console.print(f"  {status} [bold]{i}.[/bold] {question}")

    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("categories")
def categories(
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """List sherlock categories."""
    try:
        data = api_get("/sherlocks/categories/list")
        if raw:
            print_json(data)
            return

        cats = data.get("info", [])
        if not cats:
            print_warning("No categories found")
            return

        from ..formatters import create_table
        table = create_table(["ID", "Name"], "Sherlock Categories")
        for c in cats:
            table.add_row(str(c.get("id", "?")), sanitize_text(c.get("name", "?")))
        console.print(table)
    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("progress")
def progress(
    name: str = typer.Argument(..., help="Sherlock name or ID"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Show progress for a sherlock."""
    try:
        sherlock_id = _resolve_sherlock_id(name)
        data = api_get(f"/sherlocks/{sherlock_id}/progress")
        if raw:
            print_json(data)
            return

        prog = data.get("data", data)
        info = {
            "Sherlock ID": prog.get("id") or sherlock_id,
            "Name": prog.get("name"),
            "Completed Tasks": f"{prog.get('completed_tasks', 0)}/{prog.get('total_tasks', '?')}",
            "Completed": "Yes" if prog.get("completed") else "No",
            "Points Earned": prog.get("points_earned", 0),
        }
        info = {k: v for k, v in info.items() if v is not None}
        from ..formatters import print_key_value as _print_kv
        _print_kv(info, f"Sherlock Progress: {sanitize_text(prog.get('name', name))}")
    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("writeup")
def writeup(
    name: str = typer.Argument(..., help="Sherlock name or ID"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Get community writeup info for a sherlock."""
    try:
        sherlock_id = _resolve_sherlock_id(name)
        data = api_get(f"/sherlocks/{sherlock_id}/writeup")
        if raw:
            print_json(data)
            return

        wu = data.get("data", {})
        official = wu.get("official", {})
        info = {
            "PDF URL": official.get("url") or f"https://labs.hackthebox.com/api/v4/sherlocks/{sherlock_id}/writeup/official",
            "Video URL": official.get("video_url"),
        }
        info = {k: v for k, v in info.items() if v is not None}
        from ..formatters import print_key_value as _print_kv
        _print_kv(info, f"Sherlock Writeup: {name}")
    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("official-writeup")
def official_writeup(
    name: str = typer.Argument(..., help="Sherlock name or ID"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Get official writeup download URL for a sherlock."""
    try:
        sherlock_id = _resolve_sherlock_id(name)
        data = api_get(f"/sherlocks/{sherlock_id}/writeup/official")
        if raw:
            print_json(data)
            return

        url = data.get("url", "")
        if url:
            from ..formatters import console as _console
            _console.print(f"[cyan]Official Writeup URL:[/cyan] {sanitize_text(url)}")
        else:
            print_warning("No official writeup available for this sherlock")
    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)
