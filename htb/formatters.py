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

    table = create_table(["ID", "Name", "OS", "Difficulty", "Points", "Rating", "User", "Root", ""], title)

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

            name = sanitize_text(_pick(data, "name", "machine_name", "machineName", "value") or "?")
            vip = "👑" if data.get("requiredSubscription") == "VIP+" else ""

            row = [
                str(machine_id or "?"),
                name,
                sanitize_text(_pick(data, "os", "os_name", "osName") or "?"),
                sanitize_text(
                    _pick(data, "difficultyText", "difficulty_text", "difficulty", "difficultyTextShort") or "?"
                ),
                str(points),
                str(_pick(data, "star", "stars", "rating", "avg_rating", "avgRating") or "?"),
                str(user_owns),
                str(root_owns),
                vip,
            ]
            is_active = active_id is not None and machine_id is not None and int(machine_id) == active_id
            table.add_row(*row, style="green" if is_active else None)

    console.print(table)


def print_machine(machine: dict) -> None:
    """Print single machine details."""
    data = _unwrap_machine_obj(machine)

    maker = data.get("maker", {}) or {}
    maker_name = maker.get("name") if isinstance(maker, dict) else None

    user_blood = data.get("userBlood") or {}
    root_blood = data.get("rootBlood") or {}
    user_blood_name = user_blood.get("user", {}).get("name") if isinstance(user_blood, dict) else None
    root_blood_name = root_blood.get("user", {}).get("name") if isinstance(root_blood, dict) else None

    info = {
        "ID": _pick(data, "id", "machine_id", "machineId", "box_id"),
        "Name": _pick(data, "name", "machine_name", "machineName", "value"),
        "OS": _pick(data, "os", "os_name", "osName"),
        "Difficulty": _pick(data, "difficultyText", "difficulty_text", "difficulty", "difficultyTextShort"),
        "IP": _pick(data, "ip", "ip4", "ip_address") or "Not spawned",
        "Points": _pick(data, "static_points", "points", "score"),
        "Rating": _pick(data, "star", "stars", "rating", "avg_rating", "avgRating"),
        "User Owns": _pick(data, "user_owns_count", "userOwnsCount", "user_owns"),
        "Root Owns": _pick(data, "root_owns_count", "rootOwnsCount", "root_owns"),
        "Reviews": data.get("reviews_count"),
        "Free": "Yes" if _pick(data, "free", "is_free", "isFree") else "No",
        "Release": str(data.get("release", ""))[:10] if data.get("release") else None,
        "Creator": maker_name,
        "First User Blood": f"{user_blood_name} ({user_blood.get('blood_difference', '')})" if user_blood_name else None,
        "First Root Blood": f"{root_blood_name} ({root_blood.get('blood_difference', '')})" if root_blood_name else None,
        "Description": _pick(data, "synopsis", "info_status"),
        "Lab Server": _pick(data, "lab_server", "labServer") or _pick(machine, "lab_server", "labServer"),
        "VPN Server ID": _pick(data, "vpn_server_id", "vpnServerId") or _pick(machine, "vpn_server_id", "vpnServerId"),
    }

    if data.get("requiredSubscription") == "VIP+":
        info["VIP"] = "👑 Required"

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

    table = create_table(["ID", "Name", "Category", "Difficulty", "Rating", "Solves", ""], title)

    for c in challenges:
        name = sanitize_text(c.get("name", "?"))
        vip = "👑" if c.get("state") == "retired" else ""
        table.add_row(
            str(c.get("id", "?")),
            name,
            sanitize_text(c.get("category_name", c.get("category", "?"))),
            sanitize_text(c.get("difficulty", "?")),
            str(c.get("rating", "?")),
            str(c.get("solves", "?")),
            vip,
        )

    console.print(table)


def print_challenge(challenge: dict) -> None:
    """Print single challenge details."""
    data = challenge.get("data", challenge)

    solved = data.get("authUserSolve")
    solved_str = "Yes" if solved else "No"

    info = {
        "ID": data.get("id"),
        "Name": data.get("name"),
        "Category": data.get("category_name", data.get("category")),
        "Difficulty": data.get("difficulty"),
        "Points": data.get("points"),
        "Solves": data.get("solves"),
        "Rating": data.get("star", data.get("stars")),
        "Experience Points": data.get("experience_points"),
        "Likes": data.get("likes"),
        "Dislikes": data.get("dislikes"),
        "Reviews": data.get("reviews_count"),
        "State": data.get("state", "active" if not data.get("retired") else "retired"),
        "Released": str(data.get("release_date") or "")[:10] or None,
        "Creator": data.get("creator_name"),
        "First Blood": f"{data.get('first_blood_user', '')} ({data.get('first_blood_time', '')})" if data.get("first_blood_user") else None,
        "Solved": solved_str if solved is not None else None,
        "File": f"{data.get('file_name', '')} ({data.get('file_size', '')})" if data.get("file_name") else None,
        "Description": data.get("description"),
    }

    docker_ip = data.get("docker_ip") or (data.get("play_info") or {}).get("ip")
    docker_ports = data.get("docker_ports") or (data.get("play_info") or {}).get("ports")
    if docker_ip:
        port_str = f":{docker_ports[0]}" if docker_ports else ""
        info["Docker"] = f"{docker_ip}{port_str} ({data.get('docker_status', 'running')})"
    elif data.get("docker"):
        info["Docker"] = data.get("docker_status", "Not running")

    if data.get("state") == "retired" and data.get("retired"):
        info["VIP"] = "👑 Required"

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

    table = create_table(["ID", "Name", "Difficulty", "Category", "Solves", ""], title)

    for s in sherlocks:
        name = sanitize_text(s.get("name", "?"))
        vip = "👑" if s.get("state") == "retired" else ""
        table.add_row(
            str(s.get("id", "?")),
            name,
            sanitize_text(s.get("difficulty", "?")),
            sanitize_text(s.get("category_name", s.get("category", "?"))),
            str(s.get("solves", s.get("user_completions", "?"))),
            vip,
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

    if data.get("state") == "retired":
        info["VIP"] = "👑 Required"

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
# Team formatters
# ─────────────────────────────────────────────────────────────────────────────


def print_team(team: dict) -> None:
    """Print team profile."""
    info = {
        "ID": team.get("id"),
        "Name": team.get("name"),
        "Points": team.get("points"),
        "Country": team.get("country_name"),
        "Motto": team.get("motto"),
        "Captain": team.get("captain", {}).get("name") if isinstance(team.get("captain"), dict) else None,
        "Public": "[green]Yes[/green]" if team.get("public") else "No",
        "Description": team.get("description"),
    }
    info = {k: v for k, v in info.items() if v is not None}
    print_key_value(info, f"Team: {sanitize_text(team.get('name', 'Unknown'))}")


def print_team_members(members: list[dict], team_id: int) -> None:
    """Print team members."""
    if not members:
        print_warning("No members found")
        return

    table = create_table(["Name", "Rank", "Points", "Role", "Country", "Root", "User"], f"Team {team_id} Members")

    for m in members:
        table.add_row(
            sanitize_text(m.get("name", "?")),
            str(m.get("rank", m.get("rank_text", "?"))),
            str(m.get("points", "?")),
            sanitize_text(m.get("role", "?")),
            sanitize_text(m.get("country_code", m.get("country_name", "")) or ""),
            str(m.get("root_owns", "?")),
            str(m.get("user_owns", "?")),
        )

    console.print(table)


def print_team_activity(activity: list[dict], team_id: int) -> None:
    """Print team activity."""
    if not activity:
        print_warning("No recent activity")
        return

    table = create_table(["Date", "User", "Type", "Object", "Name", "Points"], f"Team {team_id} Activity")

    for a in activity:
        user_name = a.get("user", {}).get("name", "?") if isinstance(a.get("user"), dict) else "?"
        table.add_row(
            str(a.get("date_diff", a.get("date", "?"))),
            sanitize_text(user_name),
            sanitize_text(a.get("type", "?")),
            sanitize_text(a.get("object_type", "?")),
            sanitize_text(a.get("name", "?")),
            str(a.get("points", "?")),
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


_FLAG_SUCCESS_MESSAGES = (
    r"\bsuccess",
    r"\balready own",
    r"\balready owned",
    r"\bcongratulations",
    r"\bcorrect\b",
)


def _is_flag_success(message: str) -> bool:
    """Heuristic for HTB flag-submission messages that indicate success.

    The HTB API returns 4xx status codes for some flag endpoints even when the
    flag is correct (e.g. "Congratulations!", "Flag submitted successfully"),
    so we fall back on the message text when no success field is present.
    """
    import re

    msg = (message or "").lower()
    return any(re.search(token, msg) for token in _FLAG_SUCCESS_MESSAGES)


def print_flag_result(result: dict) -> None:
    """Print flag submission result."""
    message = result.get("message", "Flag accepted!")
    if result.get("success") or result.get("status") == 1 or _is_flag_success(message):
        print_success(message)
    else:
        print_error(result.get("message", "Flag rejected"))


def print_flag_submission_error(error) -> bool:
    """Handle an HTBError raised during flag submission.

    The API rejects some successful submissions with a 4xx status code, so the
    client surfaces them as HTBError. Detect success messages and print them
    as a success instead of an error.

    Returns True if the message was a real error (caller should exit non-zero),
    False if it was actually a success message.
    """
    if _is_flag_success(error.message):
        print_success(error.message)
        return False
    print_error(error.message)
    return True


# ─────────────────────────────────────────────────────────────────────────────
# Health / Infra formatters
# ─────────────────────────────────────────────────────────────────────────────


_STATUS_DOT = {
    "operational": "●",
    "partial_outage": "●",
    "major_outage": "●",
    "degraded_performance": "●",
}

_STATUS_COLOR = {
    "operational": "green",
    "partial_outage": "yellow",
    "major_outage": "red",
    "degraded_performance": "yellow",
}

_STATUS_LABEL = {
    "operational": "Operational",
    "partial_outage": "Partial Outage",
    "major_outage": "Major Outage",
    "degraded_performance": "Degraded",
}


def print_infra_health(results: list[dict]) -> None:
    """Print HTB infrastructure health status with Rich tables."""
    from rich.table import Table

    # Separate incidents from components
    incidents = [r for r in results if r.get("type") == "incident"]
    components = [r for r in results if "group" in r]

    # Group components by group name
    groups: dict[str, list[dict]] = {}
    for c in components:
        groups.setdefault(c["group"], []).append(c)

    # Overall status summary
    all_ok = all(c["status"] == "operational" for c in components)
    if all_ok and not incidents:
        console.print("[bold green]● All systems operational[/bold green]")
    elif all_ok and incidents:
        console.print("[bold yellow]● All systems operational — active incident(s)[/bold yellow]")
    else:
        degraded = [c for c in components if c["status"] != "operational"]
        names = ", ".join(c["name"] for c in degraded[:3])
        suffix = " and more" if len(degraded) > 3 else ""
        console.print(f"[bold yellow]● {len(degraded)} service(s) degraded[/bold yellow] [dim]({names}{suffix})[/dim]")
    console.print()

    # Print active incidents at top
    for inc in incidents:
        title = inc.get("title", "Unknown incident")
        console.print(Panel(
            f"[yellow]●[/yellow] [bold]{title}[/bold]",
            box=box.ROUNDED,
            border_style="yellow",
        ))
        console.print()

    # Print each service group as a table
    for group_name, group_comps in groups.items():
        table = Table(
            box=box.SIMPLE_HEAD,
            show_header=False,
            padding=(0, 2),
            border_style="dim",
        )
        table.add_column("", width=2, no_wrap=True)
        table.add_column("Service")
        table.add_column("", width=18)

        for c in group_comps:
            status = c["status"]
            dot = _STATUS_DOT.get(status, "●")
            color = _STATUS_COLOR.get(status, "white")
            label = _STATUS_LABEL.get(status, status.replace("_", " ").title())
            service_name = html.unescape(c.get("name", "?"))
            table.add_row(
                f"[{color}]{dot}[/{color}]",
                service_name,
                f"[{color}]{label}[/{color}]",
            )

        console.print(Panel(table, title=f"[bold]{group_name}[/bold]", box=box.ROUNDED, border_style="dim"))
        console.print()
