"""
Machine management commands.

Commands:
- htb machine list      - List machines
- htb machine active    - Show active machine
- htb machine info      - Get machine details
- htb machine spawn     - Spawn a machine (by name or ID)
- htb machine stop      - Terminate active machine
- htb machine reset     - Reset active machine
- htb machine own       - Submit flag
"""

from enum import Enum
from typing import Optional

import typer

from ..client import HTBError, api_get, api_post
from ..formatters import (
    console,
    print_error,
    print_flag_result,
    print_json,
    print_machine,
    print_machines,
    print_success,
    print_warning,
    sanitize_text,
)

app = typer.Typer(help="Machine management")


class Difficulty(str, Enum):
    """Machine difficulty levels."""
    easy = "easy"
    medium = "medium"
    hard = "hard"
    insane = "insane"


class SortBy(str, Enum):
    """Sort options for machine listing."""
    name = "name"
    difficulty = "difficulty"
    release = "release"
    rating = "rating"


def _find_machine_by_name(name: str) -> dict | None:
    """Find a machine by name (case-insensitive)."""
    try:
        # Try profile endpoint first (works with machine names/slugs)
        data = api_get(f"/machine/profile/{name}")
        return data.get("info", data)
    except HTBError:
        pass

    # Fallback to searching paginated list
    try:
        data = api_get("/machine/paginated", {"per_page": 100, "keyword": name})
        machines = data.get("data", [])
        name_lower = name.lower()
        for m in machines:
            if m.get("name", "").lower() == name_lower:
                return m
        return None
    except HTBError:
        return None


def _resolve_machine_id(name_or_id: str) -> int:
    """Resolve machine name or ID to numeric ID."""
    if name_or_id.isdigit():
        return int(name_or_id)

    machine = _find_machine_by_name(name_or_id)
    if machine:
        return machine["id"]

    raise HTBError(f"Machine not found: {name_or_id}")


@app.command("list")
def list_machines(
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    per_page: int = typer.Option(20, "--per-page", "-n", help="Items per page"),
    retired: bool = typer.Option(False, "--retired", help="Show retired machines"),
    sort_by: Optional[SortBy] = typer.Option(None, "--sort", "-s", help="Sort by field"),
    difficulty: Optional[Difficulty] = typer.Option(None, "--difficulty", "-d", help="Filter by difficulty"),
    search: Optional[str] = typer.Option(None, "--search", "-q", help="Search by name"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """List available machines."""
    try:
        params = {
            "page": page,
            "per_page": per_page,
        }

        if retired:
            endpoint = "/machine/list/retired/paginated"
        else:
            endpoint = "/machine/paginated"

        if sort_by:
            params["sort_by"] = sort_by.value
        if difficulty:
            params["difficulty[]"] = difficulty.value
        if search:
            params["keyword"] = search

        data = api_get(endpoint, params)

        if raw:
            print_json(data)
        else:
            machines = data.get("data", [])
            title = "Retired Machines" if retired else "Active Machines"
            print_machines(machines, title)

            # Show pagination info
            info = data.get("meta", data.get("links", {}))
            if info:
                total = info.get("total", "?")
                current = info.get("current_page", page)
                last = info.get("last_page", "?")
                console.print(f"\n[dim]Page {current}/{last} (Total: {total})[/dim]")

    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("active")
def active(
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Show currently active (spawned) machine."""
    try:
        data = api_get("/machine/active")

        if raw:
            print_json(data)
            return

        info = data.get("info")
        if not info:
            print_warning("No active machine")
            return

        print_machine(data)

    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("info")
def info(
    name: str = typer.Argument(..., help="Machine name or ID"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Get detailed information about a machine."""
    try:
        # Try profile endpoint (accepts both name and ID)
        data = api_get(f"/machine/profile/{name}")

        if raw:
            print_json(data)
        else:
            print_machine(data)

    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("spawn")
def spawn(
    name: str = typer.Argument(..., help="Machine name or ID"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Spawn a machine by name or ID."""
    try:
        machine_id = _resolve_machine_id(name)
        data = api_post("/vm/spawn", {"machine_id": machine_id})

        if raw:
            print_json(data)
        else:
            message = data.get("message", "Machine spawning...")
            print_warning("Machine spawning... IP assignment may take up to 30 seconds")
            print_success(message)

    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("stop")
def stop(
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Terminate the active machine."""
    try:
        active_data = api_get("/machine/active")
        info = active_data.get("info")

        if not info:
            print_error("No active machine to stop")
            raise typer.Exit(1)

        machine_id = info.get("id")
        data = api_post("/vm/terminate", {"machine_id": machine_id})

        if raw:
            print_json(data)
        else:
            message = data.get("message", "Machine terminated")
            print_success(message)

    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("reset")
def reset(
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Reset the active machine."""
    try:
        active_data = api_get("/machine/active")
        info = active_data.get("info")

        if not info:
            print_error("No active machine to reset")
            raise typer.Exit(1)

        machine_id = info.get("id")
        data = api_post("/vm/reset", {"machine_id": machine_id})

        if raw:
            print_json(data)
        else:
            message = data.get("message", "Machine reset initiated")
            print_success(message)

    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("own")
def own(
    flag: str = typer.Argument(..., help="Flag to submit"),
    difficulty: int = typer.Option(0, "--difficulty", "-d", help="Difficulty rating (0-100)"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Submit a flag for the active machine."""
    try:
        active_data = api_get("/machine/active")
        info = active_data.get("info")

        if not info:
            print_error("No active machine")
            raise typer.Exit(1)

        machine_id = info.get("id")

        data = api_post("/v5/machine/own", {
            "id": machine_id,
            "flag": flag,
            "difficulty": difficulty,
        })

        if raw:
            print_json(data)
        else:
            print_flag_result(data)

    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("unreleased")
def unreleased(
    per_page: int = typer.Option(10, "--per-page", "-n", help="Items per page"),
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Show upcoming unreleased machines."""
    try:
        data = api_get("/machine/unreleased", {"per_page": per_page, "page": page})

        if raw:
            print_json(data)
        else:
            machines = data.get("data", [])
            print_machines(machines, "Upcoming Machines", show_rating=False)

    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("todo")
def todo(
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Show machines on your todo list."""
    try:
        # Fetch all active machines and filter by isTodo flag
        all_todos = []
        page = 1
        while True:
            data = api_get("/machine/paginated", {"per_page": 100, "page": page})
            machines = data.get("data", [])
            all_todos.extend(m for m in machines if m.get("isTodo"))
            meta = data.get("meta", {})
            if page >= meta.get("last_page", 1):
                break
            page += 1

        if raw:
            print_json(all_todos)
        else:
            if not all_todos:
                print_warning("No machines on your todo list")
                return
            print_machines(all_todos, "Todo List")

    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("add-todo")
def add_todo(
    name: str = typer.Argument(..., help="Machine name or ID"),
):
    """Toggle a machine on your todo list."""
    try:
        machine_id = _resolve_machine_id(name)
        data = api_post(f"/machine/todo/update/{machine_id}", {})
        # Response: {"info": [{id: ...}]} when added, {"info": []} when removed
        info = data.get("info", [])
        if info:
            print_success(f"Added machine {machine_id} to todo list")
        else:
            print_success(f"Removed machine {machine_id} from todo list")

    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("writeup")
def writeup(
    name: str = typer.Argument(..., help="Machine name or ID"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Get official writeup for a retired machine."""
    try:
        machine_id = _resolve_machine_id(name)
        data = api_get(f"/machine/writeup/{machine_id}")

        if raw:
            print_json(data)
        else:
            url = data.get("url", data.get("data", {}).get("url"))
            if url:
                console.print(f"[cyan]Writeup URL:[/cyan] {sanitize_text(url)}")
            else:
                print_warning("No writeup available (machine may not be retired)")

    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)
