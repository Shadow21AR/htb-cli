"""
Challenge management commands.

Commands:
- htb challenge list       - List challenges
- htb challenge info       - Get challenge details
- htb challenge start      - Start a challenge (docker)
- htb challenge stop       - Stop a challenge
- htb challenge download   - Download challenge files
- htb challenge own        - Submit flag
- htb challenge writeup    - Get writeup for a challenge
- htb challenge activity   - Show recent solves for a challenge
"""

from enum import Enum
from pathlib import Path
from typing import List, Optional

import typer

from ..client import HTBError, api_download_bytes, api_get, api_post
from ..files import resolve_output_path
from ..formatters import (
    console,
    create_table,
    print_challenge,
    print_challenges,
    print_error,
    print_flag_result,
    print_json,
    print_key_value,
    print_success,
    print_warning,
    sanitize_text,
)

app = typer.Typer(help="Challenge management")


class Difficulty(str, Enum):
    """Challenge difficulty levels."""
    very_easy = "very-easy"
    easy = "easy"
    medium = "medium"
    hard = "hard"
    insane = "insane"


class Category(str, Enum):
    """Challenge categories."""
    ai_ml = "ai/ml"
    blockchain = "blockchain"
    coding = "coding"
    crypto = "crypto"
    forensics = "forensics"
    gamepwn = "gamepwn"
    hardware = "hardware"
    ics = "ics"
    misc = "misc"
    mobile = "mobile"
    osint = "osint"
    pwn = "pwn"
    quantum = "quantum"
    reversing = "reversing"
    satellite = "satellite"
    secure_coding = "secure coding"
    web = "web"

_CATEGORY_IDS: dict[str, int] = {
    "ai/ml": 21, "blockchain": 12, "coding": 22, "crypto": 2,
    "forensics": 7, "gamepwn": 11, "hardware": 10, "ics": 24,
    "misc": 6, "mobile": 8, "osint": 9, "pwn": 4, "quantum": 25,
    "reversing": 1, "satellite": 27, "secure coding": 23, "web": 5,
}


class ChallengeSortBy(str, Enum):
    """Sort options for challenge listing."""
    name = "name"
    release_date = "release_date"
    rating = "rating"
    user_owns = "user_owns"
    system_owns = "system_owns"
    user_difficulty = "user_difficulty"


class SortDirection(str, Enum):
    """Sort direction."""
    asc = "asc"
    desc = "desc"


def _find_challenge_by_name(name: str) -> dict | None:
    """Find a challenge by name (case-insensitive, searches all states)."""
    name_lower = name.lower()

    # Try active challenges with keyword search first
    for state in ("active", "retired", "unreleased"):
        try:
            data = api_get("/challenges", {"per_page": 100, "keyword": name, "state": state})
            for c in data.get("data", []):
                if c.get("name", "").lower() == name_lower:
                    return c
        except HTBError:
            continue

    return None


def _resolve_challenge_id(name_or_id: str) -> int:
    """Resolve challenge name or ID to numeric ID."""
    if name_or_id.isdigit():
        return int(name_or_id)

    challenge = _find_challenge_by_name(name_or_id)
    if challenge:
        return challenge["id"]

    raise HTBError(f"Challenge not found: {name_or_id}")


@app.command("list")
def list_challenges(
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    per_page: int = typer.Option(20, "--per-page", "-n", help="Items per page"),
    state: Optional[str] = typer.Option(None, "--state", help="Filter by state (active, retired, unreleased)"),
    category: Optional[List[Category]] = typer.Option(None, "--category", "-c", help="Filter by category (use multiple times)"),
    difficulty: Optional[List[Difficulty]] = typer.Option(None, "--difficulty", "-d", help="Filter by difficulty (use multiple times)"),
    search: Optional[str] = typer.Option(None, "--search", "-q", help="Search by name"),
    todo: bool = typer.Option(False, "--todo", "-t", help="Todo-listed challenges only"),
    completed: bool = typer.Option(False, "--completed", help="Show only completed challenges"),
    incomplete: bool = typer.Option(False, "--incomplete", help="Show only incomplete challenges"),
    sort_by: Optional[ChallengeSortBy] = typer.Option(None, "--sort", "-s", help="Sort by field (name, release-date, rating, etc.)"),
    sort_type: Optional[SortDirection] = typer.Option(None, "--sort-type", help="Sort direction"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """List available challenges."""
    try:
        params: dict = {
            "page": page,
            "per_page": per_page,
        }
        if state:
            params["state"] = state
        if difficulty:
            params["difficulty[]"] = [d.value for d in difficulty]
        if category:
            params["category[]"] = [_CATEGORY_IDS[c.value] for c in category]
        if search:
            params["keyword"] = search
        if todo:
            params["todo"] = "1"
        if completed:
            params["completed"] = "1"
        if incomplete:
            params["status"] = "incompleted"
        if sort_by:
            params["sort_by"] = sort_by.value
        if sort_type:
            params["sort_type"] = sort_type.value

        data = api_get("/challenges", params)

        if raw:
            print_json(data)
            return

        challenges = data.get("data", [])

        # Build category name map if missing
        if challenges and "category_name" not in challenges[0]:
            try:
                cats_data = api_get("/challenge/categories/list")
                cat_map = {c["id"]: c["name"] for c in cats_data.get("info", [])}
                for c in challenges:
                    c["category_name"] = cat_map.get(c.get("challenge_category_id"), "Unknown")
            except HTBError:
                pass

        if not challenges:
            print_warning("No challenges found")
            return

        print_challenges(challenges, "Challenges")

        meta = data.get("meta", {})
        if meta:
            current = meta.get("current_page", page)
            last = meta.get("last_page", "?")
            total = meta.get("total", "?")
            console.print(f"\n[dim]Page {current}/{last} (Total: {total})[/dim]")

    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("categories")
def categories(
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """List challenge categories."""
    try:
        data = api_get("/challenge/categories/list")

        if raw:
            print_json(data)
            return

        cats = data.get("info", data.get("data", []))
        if not cats:
            print_warning("No categories found")
            return

        console.print("[bold cyan]Challenge Categories[/bold cyan]")
        for cat in cats:
            name = cat.get("name", cat) if isinstance(cat, dict) else cat
            console.print(f"  • {sanitize_text(name)}")

    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("info")
def info(
    name: str = typer.Argument(..., help="Challenge name or ID"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Get detailed information about a challenge."""
    try:
        challenge_id = _resolve_challenge_id(name)
        data = api_get(f"/challenge/info/{challenge_id}")

        if raw:
            print_json(data)
        else:
            print_challenge(data.get("challenge", data))

    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("start")
def start(
    name: str = typer.Argument(..., help="Challenge name or ID"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Start a challenge (spawn docker container)."""
    try:
        challenge_id = _resolve_challenge_id(name)
        data = api_post("/container/start", {"challenge_id": challenge_id})

        if raw:
            print_json(data)
        else:
            ip = data.get("ip", data.get("data", {}).get("ip"))
            port = data.get("port", data.get("data", {}).get("port"))
            if ip:
                print_success(f"Challenge started: {ip}:{port}" if port else f"Challenge started: {ip}")
            else:
                print_success(data.get("message", "Challenge started"))

    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("stop")
def stop(
    name: Optional[str] = typer.Argument(None, help="Challenge name or ID (optional, auto-detects active docker)"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Stop a running challenge."""
    try:
        if name:
            challenge_id = _resolve_challenge_id(name)
        else:
            data = api_get("/challenge/list")
            all_challenges = data.get("challenges", data.get("data", []))
            running = [c for c in all_challenges if c.get("isActive")]
            if not running:
                print_error("No active challenge. Specify challenge name or ID.")
                raise typer.Exit(1)
            challenge_id = running[0]["id"]

        data = api_post("/container/stop", {"challenge_id": challenge_id})

        if raw:
            print_json(data)
        else:
            print_success(data.get("message", "Challenge stopped"))

    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("download")
def download(
    name: str = typer.Argument(..., help="Challenge name or ID"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path"),
):
    """Download challenge files."""
    try:
        challenge_id = _resolve_challenge_id(name)

        try:
            content = api_download_bytes(f"/challenge/download/{challenge_id}")
        except HTBError as e:
            if e.status_code == 404:
                print_warning("No files to download for this challenge")
            else:
                print_error(e.message)
            raise typer.Exit(1)

        # Get challenge name for filename if not specified
        try:
            info_data = api_get(f"/challenge/info/{challenge_id}")
            challenge_name = info_data.get("challenge", {}).get("name", f"challenge_{challenge_id}")
        except Exception:
            challenge_name = f"challenge_{challenge_id}"

        filename = f"{challenge_name}.zip"
        path = resolve_output_path(output, filename)
        path.write_bytes(content)
        print_success(f"Downloaded to: {path}")

    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("own")
def own(
    flag: str = typer.Argument(..., help="Flag to submit"),
    name: Optional[str] = typer.Option(None, "--challenge", "-c", help="Challenge name or ID (auto-detects if docker running)"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Submit a flag for a challenge."""
    try:
        if name:
            challenge_id = _resolve_challenge_id(name)
        else:
            # Find active challenge by scanning for isActive flag
            data = api_get("/challenge/list")
            all_challenges = data.get("challenges", data.get("data", []))
            running = [c for c in all_challenges if c.get("isActive")]
            if running:
                challenge_id = running[0]["id"]
            else:
                print_error("No active challenge. Specify with --challenge")
                raise typer.Exit(1)

        data = api_post("/challenge/own", {
            "challenge_id": challenge_id,
            "flag": flag,
        })

        if raw:
            print_json(data)
        else:
            print_flag_result(data)

    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("active")
def active(
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Show your currently running challenge docker instance."""
    try:
        data = api_get("/challenge/list")
        challenges = data.get("challenges", data.get("data", []))
        running = [c for c in challenges if c.get("isActive")]

        if raw:
            print_json(running)
            return

        if not running:
            print_warning("No active challenge")
            return

        # Enrich with docker/connection details from info endpoint
        for c in running:
            try:
                info_data = api_get(f"/challenge/info/{c['id']}")
                chal = info_data.get("challenge", info_data)
                c.update(chal)
            except HTBError:
                pass

        for c in running:
            docker_ip = c.get("docker_ip") or (c.get("play_info") or {}).get("ip")
            docker_ports = c.get("docker_ports") or (c.get("play_info") or {}).get("ports")
            info = {
                "ID": c.get("id"),
                "Name": c.get("name"),
                "State": c.get("state", "active"),
            }
            if docker_ip:
                port_str = f":{docker_ports[0]}" if docker_ports else ""
                info["Docker"] = f"{docker_ip}{port_str}"
            print_key_value(info, f"Active Challenge: {sanitize_text(c.get('name', 'Unknown'))}")

    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("writeup")
def writeup(
    name: str = typer.Argument(..., help="Challenge name or ID"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Get writeup for a challenge."""
    try:
        challenge_id = _resolve_challenge_id(name)
        data = api_get(f"/challenge/{challenge_id}/writeup")

        if raw:
            print_json(data)
        else:
            official = data.get("data", {}).get("official", {})
            api_url = official.get("url")
            if not api_url:
                print_warning("No writeup available")
                return

            # Fetch the actual download URL from the official endpoint
            dl_data = api_get(f"/challenge/{challenge_id}/writeup/official")
            dl_url = dl_data.get("url")
            filename = official.get("filename", "writeup.pdf")
            if dl_url:
                console.print(f"[cyan]Writeup:[/cyan] {sanitize_text(filename)}")
                console.print(f"[cyan]Download:[/cyan] {sanitize_text(dl_url)}")
            else:
                console.print(f"[cyan]Writeup URL:[/cyan] {sanitize_text(api_url)}")

    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("activity")
def activity(
    name: str = typer.Argument(..., help="Challenge name or ID"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Show recent solves for a challenge."""
    try:
        challenge_id = _resolve_challenge_id(name)
        data = api_get(f"/challenge/activity/{challenge_id}")

        if raw:
            print_json(data)
        else:
            activity_list = data.get("info", {}).get("activity", [])
            activity_list.reverse()
            if not activity_list:
                print_warning("No activity found")
                return

            table = create_table(["When", "User", "Type"], "Challenge Activity")
            for a in activity_list:
                table.add_row(
                    a.get("date_diff", "?"),
                    sanitize_text(a.get("user_name", "?")),
                    a.get("type", "?"),
                )
            console.print(table)

    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)
