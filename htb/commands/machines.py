"""
Machine management commands.

Commands:
- htb machine list         - List machines (--state, --todo, --difficulty, --search, --sort)
- htb machine active       - Show active machine
- htb machine info         - Get machine details
- htb machine spawn NAME   - Spawn a machine
- htb machine stop         - Terminate active machine
- htb machine reset        - Reset active machine
- htb machine own FLAG     - Submit flag
- htb machine add-todo NAME - Toggle machine on todo list
- htb machine writeup NAME - Get official writeup URL
- htb machine achievement NAME - Print achievement URL
"""

from enum import Enum
from typing import List, Optional

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

def _is_auth_error(e: HTBError) -> bool:
    # Covers both API auth errors and local token-missing error wrapped as HTBError.
    msg = (e.message or "").lower()
    return "no htb token found" in msg or "authentication failed" in msg


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
    points = "points"


class MachineState(str, Enum):
    """Machine list state filter."""
    active = "active"
    retired = "retired"
    unreleased = "unreleased"


class OsFilter(str, Enum):
    """OS filter options."""
    windows = "windows"
    linux = "linux"
    freebsd = "freebsd"
    solaris = "solaris"


class SortType(str, Enum):
    """Sort direction."""
    asc = "asc"
    desc = "desc"


def _find_machine_by_name(name: str) -> dict | None:
    """Find a machine by name (case-insensitive)."""
    try:
        # Try profile endpoint first (works with machine names/slugs)
        data = api_get(f"/machine/profile/{name}")
        return data.get("info", data)
    except HTBError as e:
        # Do not mask auth/token errors as "not found".
        if _is_auth_error(e):
            raise
        pass

    # Fallback to searching v5 machine list
    try:
        data = api_get("/v5/machines", {"per_page": 100, "keyword": name})
        machines = data.get("data", [])
        name_lower = name.lower()
        for m in machines:
            if m.get("name", "").lower() == name_lower:
                return m
        return None
    except HTBError as e:
        if _is_auth_error(e):
            raise
        return None


def _resolve_machine_id(name_or_id: str) -> int:
    """Resolve machine name or ID to numeric ID."""
    if name_or_id.isdigit():
        return int(name_or_id)

    machine = _find_machine_by_name(name_or_id)
    if machine:
        return machine["id"]

    raise HTBError(f"Machine not found: {name_or_id}")

def _resolve_user_id() -> int:
    """Resolve current user ID via /user/info."""
    data = api_get("/user/info")
    info = data.get("info", {})
    user_id = info.get("id")
    if not user_id:
        raise HTBError("Could not determine user ID from /user/info")
    return int(user_id)


@app.command("list")
def list_machines(
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    per_page: int = typer.Option(20, "--per-page", "-n", help="Items per page"),
    state: MachineState = typer.Option(
        MachineState.active, "--state", help="Filter by state (active, retired, unreleased)"
    ),
    difficulty: Optional[Difficulty] = typer.Option(None, "--difficulty", "-d", help="Filter by difficulty"),
    os: Optional[List[OsFilter]] = typer.Option(None, "--os", help="Filter by OS (use multiple times: --os linux --os windows)"),
    search: Optional[str] = typer.Option(None, "--search", "-q", help="Search by name"),
    free: bool = typer.Option(False, "--free", help="Free machines only"),
    todo: bool = typer.Option(False, "--todo", "-t", help="Todo-listed machines only"),
    completed: bool = typer.Option(False, "--completed", help="Show only completed machines"),
    incomplete: bool = typer.Option(False, "--incomplete", help="Show only incomplete machines"),
    sort_by: Optional[SortBy] = typer.Option(None, "--sort", "-s", help="Sort by field (name, difficulty, release, rating, points)"),
    sort_type: Optional[SortType] = typer.Option(None, "--sort-type", help="Sort direction (asc, desc)"),
    sp_tier: Optional[int] = typer.Option(None, "--sp-tier", help="Starting Point tier ID"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """List available machines."""
    try:
        params = {
            "page": page,
            "per_page": per_page,
            "state": state.value,
        }
        if difficulty:
            params["difficulty"] = difficulty.value
        if os:
            params["os[]"] = [o.value for o in os]
        if search:
            params["keyword"] = search
        if free:
            params["free"] = "1"
        if todo:
            params["todo"] = "1"
        if completed:
            params["showCompleted"] = "complete"
        if incomplete:
            params["showCompleted"] = "incomplete"
        if sort_by:
            params["sort_by"] = sort_by.value
        if sort_type:
            params["sort_type"] = sort_type.value
        if sp_tier is not None:
            params["sp_tier"] = str(sp_tier)

        data = api_get("/v5/machines", params)

        if raw:
            print_json(data)
            return

        machines = data.get("data", [])
        title = f"{state.value.title()} Machines"

        if not machines:
            print_warning(f"No {state.value} machines found")
            return

        try:
            active_data = api_get("/v5/virtual_machine/active")
            active_info = active_data.get("info") or {}
            active_id = active_info.get("id")
        except HTBError:
            active_id = None

        print_machines(machines, title, active_id=active_id)

        meta = data.get("meta", {})
        if meta:
            current = meta.get("current_page", page)
            last = meta.get("last_page", "?")
            total = meta.get("total", "?")
            console.print(f"\n[dim]Page {current}/{last} (Total: {total})[/dim]")

    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)

@app.command("achievement")
def achievement(
    name: Optional[str] = typer.Argument(None, help="Machine name or ID (default: active machine)"),
    user_id: Optional[int] = typer.Option(
        None, "--user-id", help="Override user ID (defaults to current user)"
    ),
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Print shareable achievement URL for a machine."""
    try:
        if name:
            machine_id = _resolve_machine_id(name)
            target_name = name
        else:
            active_data = api_get("/machine/active")
            info = active_data.get("info") if isinstance(active_data, dict) else None
            if not info:
                raise HTBError("No active machine")
            machine_id = info.get("id")
            if not machine_id:
                raise HTBError("Could not determine active machine ID")
            target_name = info.get("name") or "active"

        resolved_user_id = int(user_id) if user_id is not None else _resolve_user_id()

        url = f"https://labs.hackthebox.com/achievement/machine/{resolved_user_id}/{machine_id}"

        if raw:
            print_json(
                {
                    "target_type": "machine",
                    "user_id": resolved_user_id,
                    "target_id": machine_id,
                    "target_name": target_name,
                    "url": url,
                }
            )
            return

        console.print(f"[cyan]Achievement URL:[/cyan] {sanitize_text(url)}")

    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("active")
def active(
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Show currently active (spawned) machine."""
    try:
        data = api_get("/v5/virtual_machine/active")

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


@app.command("add-todo")
def add_todo(
    name: str = typer.Argument(..., help="Machine name or ID"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Toggle a machine on your todo list."""
    try:
        machine_id = _resolve_machine_id(name)
        data = api_post(f"/machine/todo/update/{machine_id}", {})

        if raw:
            print_json(data)
            return

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
