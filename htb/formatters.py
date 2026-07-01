"""
Output formatters for HTB CLI.

Provides consistent, beautiful output using Rich.
"""

import html
import json
import unicodedata
from typing import Any

from rich import box
from rich.console import Console
from rich.markup import escape as rich_escape
from rich.panel import Panel
from rich.table import Table

console = Console()

def _pick(d: dict, *keys: str):
    """Return the first present (non-None) value for any key in keys."""
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return None


def _unwrap_machine_obj(obj: Any) -> dict:
    """
    Best-effort normalization for machine-ish payloads across endpoints.

    Some endpoints return bare machine dicts, others wrap under "data"/"info",
    and season endpoints may nest under "machine"/"box".
    """
    if not isinstance(obj, dict):
        return {}

    # Common wrappers
    if isinstance(obj.get("data"), dict):
        obj = obj["data"]
    if isinstance(obj.get("info"), dict):
        obj = obj["info"]

    # Season-like wrappers
    for k in ("machine", "box"):
        v = obj.get(k)
        if isinstance(v, dict):
            obj = v
            if isinstance(obj.get("info"), dict):
                obj = obj["info"]
            break

    return obj if isinstance(obj, dict) else {}


def sanitize_text(value: Any) -> str:
    """Strip non-printable and control characters from a value, keeping normal text."""
    s = html.unescape(html.unescape(str(value)))
    cleaned = "".join(
        ch for ch in s
        if ch == "\n" or (not unicodedata.category(ch).startswith("C"))
    )
    return rich_escape(cleaned)


def print_json(data: Any) -> None:
    """Print raw JSON output."""
    console.print_json(json.dumps(data, indent=2, default=str))


def print_error(message: str) -> None:
    """Print error message."""
    console.print(f"[red]Error:[/red] {message}")


def print_success(message: str) -> None:
    """Print success message."""
    console.print(f"[green]✓[/green] {message}")


def print_warning(message: str) -> None:
    """Print warning message."""
    console.print(f"[yellow]Warning:[/yellow] {message}")


def print_info(message: str) -> None:
    """Print info message."""
    console.print(f"[blue]→[/blue] {message}")


def print_key_value(data: dict[str, Any], title: str | None = None) -> None:
    """Print key-value pairs in a panel."""
    lines = []
    for key, value in data.items():
        lines.append(f"[cyan]{key}:[/cyan] {sanitize_text(value)}")

    content = "\n".join(lines)
    if title:
        console.print(Panel(content, title=sanitize_text(title), box=box.ROUNDED))
    else:
        console.print(content)


def create_table(columns: list[str], title: str | None = None) -> Table:
    """Create a table with standard styling."""
    table = Table(
        title=title,
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
    )
    for col in columns:
        table.add_column(col)
    return table


# ─────────────────────────────────────────────────────────────────────────────
# Machine formatters
# ─────────────────────────────────────────────────────────────────────────────


def print_machines(machines: list[dict], title: str = "Machines", active_id: int | None = None) -> None:
    """Print machine list in a table."""
    if not machines:
        print_warning("No machines found")
        return

    table = create_table(["ID", "Name", "OS", "Difficulty", "Points", "Rating", "User", "Root"], title)

    for m in machines:
        data = _unwrap_machine_obj(m)
        if data:
            points = _pick(data, "points")
            if points is None:
                user_pts = data.get("user_points")
                root_pts = data.get("root_points")
                if user_pts is not None and root_pts is not None:
                    points = user_pts + root_pts
                else:
                    points = "?"
            user_owns = _pick(data, "userOwnsCount", "user_owns_count", "user_owns") or ""
            root_owns = _pick(data, "rootOwnsCount", "root_owns_count", "root_owns") or ""
            machine_id = _pick(data, "id", "machine_id", "machineId", "box_id")

            row = [
                str(machine_id or "?"),
                sanitize_text(_pick(data, "name", "machine_name", "machineName", "value") or "?"),
                sanitize_text(_pick(data, "os", "os_name", "osName") or "?"),
                sanitize_text(
                    _pick(data, "difficultyText", "difficulty_text", "difficulty", "difficultyTextShort") or "?"
                ),
                str(points),
                str(_pick(data, "star", "stars", "rating", "avg_rating", "avgRating") or "?"),
                str(user_owns),
                str(root_owns),
            ]
            is_active = active_id is not None and machine_id is not None and int(machine_id) == active_id
            table.add_row(*row, style="green" if is_active else None)

    console.print(table)


def print_machine(machine: dict) -> None:
    """Print single machine details."""
    data = _unwrap_machine_obj(machine)

    info = {
        "ID": _pick(data, "id", "machine_id", "machineId", "box_id"),
        "Name": _pick(data, "name", "machine_name", "machineName", "value"),
        "OS": _pick(data, "os", "os_name", "osName"),
        "Difficulty": _pick(data, "difficultyText", "difficulty_text", "difficulty", "difficultyTextShort"),
        "IP": _pick(data, "ip", "ip4", "ip_address") or "Not spawned",
        "Rating": _pick(data, "star", "stars", "rating", "avg_rating", "avgRating"),
        "Points": _pick(data, "points", "score"),
        "Description": _pick(data, "info_status", "synopsis"),
        "Lab Server": _pick(data, "lab_server", "labServer") or _pick(machine, "lab_server", "labServer"),
        "VPN Server ID": _pick(data, "vpn_server_id", "vpnServerId") or _pick(machine, "vpn_server_id", "vpnServerId"),
    }

    info = {k: v for k, v in info.items() if v is not None}
    title_name = _pick(data, "name", "machine_name", "machineName", "value") or "Unknown"
    print_key_value(info, f"Machine: {sanitize_text(title_name)}")


# ─────────────────────────────────────────────────────────────────────────────
# Challenge formatters
# ─────────────────────────────────────────────────────────────────────────────


def print_challenges(challenges: list[dict], title: str = "Challenges") -> None:
    """Print challenge list in a table."""
    if not challenges:
        print_warning("No challenges found")
        return

    table = create_table(["ID", "Name", "Category", "Difficulty", "Rating", "Solves"], title)

    for c in challenges:
        table.add_row(
            str(c.get("id", "?")),
            sanitize_text(c.get("name", "?")),
            sanitize_text(c.get("category_name", c.get("category", "?"))),
            sanitize_text(c.get("difficulty", "?")),
            str(c.get("rating", "?")),
            str(c.get("solves", "?")),
        )

    console.print(table)


def print_challenge(challenge: dict) -> None:
    """Print single challenge details."""
    data = challenge.get("data", challenge)

    info = {
        "ID": data.get("id"),
        "Name": data.get("name"),
        "Category": data.get("category_name", data.get("category")),
        "Difficulty": data.get("difficulty"),
        "Points": data.get("points"),
        "Solves": data.get("solves"),
        "Rating": data.get("star", data.get("stars")),
        "Released": str(data.get("release_date") or data.get("released") or "")[:10] or None,
        "Description": data.get("description"),
    }

    info = {k: v for k, v in info.items() if v is not None}
    print_key_value(info, f"Challenge: {sanitize_text(data.get('name', 'Unknown'))}")


# ─────────────────────────────────────────────────────────────────────────────
# Sherlock formatters
# ─────────────────────────────────────────────────────────────────────────────


def print_sherlocks(sherlocks: list[dict], title: str = "Sherlocks") -> None:
    """Print sherlock list in a table."""
    if not sherlocks:
        print_warning("No sherlocks found")
        return

    table = create_table(["ID", "Name", "Difficulty", "Category", "Solves"], title)

    for s in sherlocks:
        table.add_row(
            str(s.get("id", "?")),
            sanitize_text(s.get("name", "?")),
            sanitize_text(s.get("difficulty", "?")),
            sanitize_text(s.get("category_name", s.get("category", "?"))),
            str(s.get("solves", s.get("user_completions", "?"))),
        )

    console.print(table)


def print_sherlock(sherlock: dict) -> None:
    """Print single sherlock details."""
    data = sherlock.get("data", sherlock)

    info = {
        "ID": data.get("id"),
        "Name": data.get("name"),
        "Difficulty": data.get("difficulty"),
        "Category": data.get("category_name", data.get("category")),
        "Solves": data.get("solves", data.get("user_completions")),
        "Description": data.get("description"),
    }

    info = {k: v for k, v in info.items() if v is not None}
    print_key_value(info, f"Sherlock: {sanitize_text(data.get('name', 'Unknown'))}")


# ─────────────────────────────────────────────────────────────────────────────
# Fortress formatters
# ─────────────────────────────────────────────────────────────────────────────


def print_fortresses(fortresses: list[dict], title: str = "Fortresses") -> None:
    """Print fortress list in a table."""
    if not fortresses:
        print_warning("No fortresses found")
        return

    table = create_table(["ID", "Name", "Flags", "Owned"], title)

    for f in fortresses:
        owned_f = f.get("owned_flags", 0)
        total_f = f.get("number_of_flags", "?")
        owned_str = f"{owned_f}/{total_f}"
        table.add_row(
            str(f.get("id", "?")),
            sanitize_text(f.get("name", "?")),
            str(total_f),
            owned_str,
        )

    console.print(table)


def print_fortress(fortress: dict) -> None:
    """Print single fortress details."""
    info = {
        "ID": fortress.get("id"),
        "Name": fortress.get("name"),
        "IP": fortress.get("ip"),
        "Flags": fortress.get("num_flags", fortress.get("number_of_flags")),
        "Points": fortress.get("points"),
        "Company": fortress.get("company", {}).get("name") if isinstance(fortress.get("company"), dict) else None,
        "Reset Votes": fortress.get("reset_votes"),
        "Progress": fortress.get("progress_percent", fortress.get("progress")),
        "Players Completed": fortress.get("players_completed"),
        "Description": fortress.get("description"),
    }

    info = {k: v for k, v in info.items() if v is not None}
    print_key_value(info, f"Fortress: {sanitize_text(fortress.get('name', 'Unknown'))}")


# ─────────────────────────────────────────────────────────────────────────────
# Track formatters
# ─────────────────────────────────────────────────────────────────────────────


def print_tracks(tracks: list[dict], title: str = "Tracks") -> None:
    """Print track list in a table."""
    if not tracks:
        print_warning("No tracks found")
        return

    table = create_table(["ID", "Name", "Difficulty", "Likes", "Official"], title)

    for t in tracks:
        table.add_row(
            str(t.get("id", "?")),
            sanitize_text(t.get("name", "?")),
            sanitize_text(t.get("difficulty", "?")),
            str(t.get("likes", "?")),
            "[green]✓[/green]" if t.get("official") else "[dim]○[/dim]",
        )

    console.print(table)


def print_track(track: dict) -> None:
    """Print single track details."""
    info = {
        "ID": track.get("id"),
        "Name": track.get("name"),
        "Difficulty": track.get("difficulty"),
        "Creator": track.get("creator", {}).get("name") if isinstance(track.get("creator"), dict) else None,
        "Likes": track.get("likes"),
        "Official": "[green]Yes[/green]" if track.get("official") else "No",
        "Staff Pick": "[green]Yes[/green]" if track.get("staff_pick") else "No",
        "Description": track.get("description"),
    }

    info = {k: v for k, v in info.items() if v is not None}
    print_key_value(info, f"Track: {sanitize_text(track.get('name', 'Unknown'))}")

    # Show items/modules in the track
    items = track.get("items", [])
    if items:
        from rich.table import Table
        table = Table(title="Modules", box=box.ROUNDED, show_header=True, header_style="bold cyan")
        table.add_column("#")
        table.add_column("Type")
        table.add_column("Name")
        table.add_column("Difficulty")
        table.add_column("Completed")
        for i, item in enumerate(items, 1):
            completed = "[green]✓[/green]" if item.get("complete") else "[dim]○[/dim]"
            table.add_row(
                str(i),
                sanitize_text(item.get("type", "?")),
                sanitize_text(item.get("name", "?")),
                sanitize_text(item.get("difficulty", "?")),
                completed,
            )
        console.print()
        console.print(table)


# ─────────────────────────────────────────────────────────────────────────────
# Ranking formatters
# ─────────────────────────────────────────────────────────────────────────────


def print_ranking_entries(entries: list[dict], title: str = "Rankings") -> None:
    """Print ranking entries (users or teams) in a table."""
    if not entries:
        print_warning("No entries found")
        return

    table = create_table(["Rank", "Name", "Country", "Points", "Root", "User", "Challenges", "Fortress"], title)

    for e in entries:
        table.add_row(
            str(e.get("rank", "?")),
            sanitize_text(e.get("name", "?")),
            sanitize_text(e.get("country", e.get("country_code", "")) or ""),
            str(e.get("points", "?")),
            str(e.get("root_owns", "?")),
            str(e.get("user_owns", "?")),
            str(e.get("challenge_owns", "?")),
            str(e.get("fortress", "?")),
        )

    console.print(table)


def print_countries(entries: list[dict], title: str = "Country Rankings") -> None:
    """Print country rankings."""
    if not entries:
        print_warning("No entries found")
        return

    table = create_table(["Rank", "Country", "Code", "Members", "Points", "Root", "User", "Challenges"], title)

    for e in entries:
        table.add_row(
            str(e.get("rank", "?")),
            sanitize_text(e.get("name", "?")),
            sanitize_text(e.get("country", "?")),
            str(e.get("members", "?")),
            str(e.get("points", "?")),
            str(e.get("root_owns", "?")),
            str(e.get("user_owns", "?")),
            str(e.get("challenge_owns", "?")),
        )

    console.print(table)


def print_universities(entries: list[dict], title: str = "University Rankings") -> None:
    """Print university rankings."""
    if not entries:
        print_warning("No entries found")
        return

    table = create_table(["Rank", "Name", "Country", "Students", "Points", "Root", "User", "Challenges"], title)

    for e in entries:
        table.add_row(
            str(e.get("rank", "?")),
            sanitize_text(e.get("name", "?")),
            sanitize_text(e.get("country", "") or ""),
            str(e.get("students", "?")),
            str(e.get("points", "?")),
            str(e.get("root_owns", "?")),
            str(e.get("user_owns", "?")),
            str(e.get("challenge_owns", "?")),
        )

    console.print(table)


def print_country_members(entries: list[dict], country_code: str) -> None:
    """Print country member rankings."""
    if not entries:
        print_warning("No members found")
        return

    table = create_table(["Rank", "Name", "Points", "Root", "User", "Challenges"], f"Country Members: {country_code.upper()}")

    for e in entries:
        table.add_row(
            str(e.get("rank", "?")),
            sanitize_text(e.get("name", "?")),
            str(e.get("points", "?")),
            str(e.get("root_owns", "?")),
            str(e.get("user_owns", "?")),
            str(e.get("challenge_owns", "?")),
        )

    console.print(table)


# ─────────────────────────────────────────────────────────────────────────────
# VPN/Connection formatters
# ─────────────────────────────────────────────────────────────────────────────


def print_servers(servers: list[dict], title: str = "VPN Servers") -> None:
    """Print VPN server list."""
    if not servers:
        print_warning("No servers found")
        return

    table = create_table(["ID", "Name", "Location", "Users"], title)

    for srv in servers:
        table.add_row(
            str(srv.get("id", "?")),
            sanitize_text(srv.get("friendly_name", srv.get("name", "?"))),
            sanitize_text(srv.get("location", "?")),
            str(srv.get("current_clients", "?")),
        )

    console.print(table)


def print_connection_status(status: dict | list) -> None:
    """Print connection status."""
    if isinstance(status, list):
        if not status:
            print_warning("No active connections")
            return
        status = status[0]

    data = status.get("data", status)

    info = {
        "Type": data.get("type", data.get("location_type_friendly")),
        "Server": data.get("server", {}).get("friendly_name") if isinstance(data.get("server"), dict) else None,
        "Server ID": data.get("server", {}).get("id") if isinstance(data.get("server"), dict) else None,
        "IP": data.get("connection", {}).get("ip4") if isinstance(data.get("connection"), dict) else data.get("ip"),
        "Location": data.get("location_type_friendly"),
    }

    info = {k: v for k, v in info.items() if v is not None}

    if info:
        print_key_value(info, "Connection Status")
    else:
        print_warning("No active connection")


# ─────────────────────────────────────────────────────────────────────────────
# Flag/Result formatters
# ─────────────────────────────────────────────────────────────────────────────


def print_flag_result(result: dict) -> None:
    """Print flag submission result."""
    if result.get("success") or result.get("status") == 1:
        print_success(result.get("message", "Flag accepted!"))
    else:
        print_error(result.get("message", "Flag rejected"))
