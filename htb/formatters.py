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
from rich.panel import Panel
from rich.table import Table

console = Console()


def sanitize_text(value: Any) -> str:
    """Strip non-printable and control characters from a value, keeping normal text."""
    s = html.unescape(html.unescape(str(value)))
    return "".join(
        ch for ch in s
        if ch == "\n" or (not unicodedata.category(ch).startswith("C"))
    )


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


def print_machines(machines: list[dict], title: str = "Machines", show_rating: bool = True) -> None:
    """Print machine list in a table."""
    if not machines:
        print_warning("No machines found")
        return

    if show_rating:
        columns = ["ID", "Name", "OS", "Difficulty", "Rating", "Free"]
    else:
        columns = ["ID", "Name", "OS", "Difficulty"]
    table = create_table(columns, title)

    for m in machines:
        data = m.get("data", m)
        if isinstance(data, dict):
            row = [
                str(data.get("id", "?")),
                sanitize_text(data.get("name", "?")),
                sanitize_text(data.get("os", "?")),
                sanitize_text(data.get("difficultyText", data.get("difficulty", "?"))),
            ]
            if show_rating:
                row.append(str(data.get("star", data.get("rating", "?"))))
                row.append("✓" if data.get("free") else "✗")
            table.add_row(*row)

    console.print(table)


def print_machine(machine: dict) -> None:
    """Print single machine details."""
    data = machine.get("data", machine).get("info", machine.get("data", machine))

    info = {
        "ID": data.get("id"),
        "Name": data.get("name"),
        "OS": data.get("os"),
        "Difficulty": data.get("difficultyText", data.get("difficulty")),
        "IP": data.get("ip", "Not spawned"),
        "Rating": data.get("star", data.get("stars")),
        "Points": data.get("points"),
    }

    info = {k: v for k, v in info.items() if v is not None}
    print_key_value(info, f"Machine: {sanitize_text(data.get('name', 'Unknown'))}")


# ─────────────────────────────────────────────────────────────────────────────
# Challenge formatters
# ─────────────────────────────────────────────────────────────────────────────


def print_challenges(challenges: list[dict], title: str = "Challenges") -> None:
    """Print challenge list in a table."""
    if not challenges:
        print_warning("No challenges found")
        return

    table = create_table(["ID", "Name", "Category", "Difficulty", "Points", "Solves"], title)

    for c in challenges:
        table.add_row(
            str(c.get("id", "?")),
            sanitize_text(c.get("name", "?")),
            sanitize_text(c.get("category_name", c.get("category", "?"))),
            sanitize_text(c.get("difficulty", "?")),
            str(c.get("points", "?")),
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
