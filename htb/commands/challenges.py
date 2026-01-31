"""
Challenge management commands.

Commands:
- htb challenge list       - List challenges
- htb challenge info       - Get challenge details
- htb challenge start      - Start a challenge (docker)
- htb challenge stop       - Stop a challenge
- htb challenge download   - Download challenge files
- htb challenge own        - Submit flag
"""

from enum import Enum
from pathlib import Path
from typing import Optional

import typer

from ..client import HTBError, api_download_bytes, api_get, api_post
from ..formatters import (
    console,
    print_challenge,
    print_challenges,
    print_error,
    print_flag_result,
    print_json,
    print_success,
    print_warning,
    sanitize_text,
)

app = typer.Typer(help="Challenge management")


class Difficulty(str, Enum):
    """Challenge difficulty levels."""
    very_easy = "very_easy"
    easy = "easy"
    medium = "medium"
    hard = "hard"
    insane = "insane"


class Category(str, Enum):
    """Challenge categories."""
    reversing = "reversing"
    crypto = "crypto"
    pwn = "pwn"
    web = "web"
    forensics = "forensics"
    misc = "misc"
    mobile = "mobile"
    osint = "osint"
    hardware = "hardware"
    blockchain = "blockchain"
    ai_ml = "ai - ml"
    coding = "coding"
    gamepwn = "gamepwn"
    ics = "ics"
    quantum = "quantum"
    secure_coding = "secure coding"


def _find_challenge_by_name(name: str) -> dict | None:
    """Find a challenge by name (case-insensitive)."""
    try:
        data = api_get("/challenge/list")
        challenges = data.get("challenges", data.get("data", []))
        name_lower = name.lower()
        for c in challenges:
            if c.get("name", "").lower() == name_lower:
                return c
        return None
    except HTBError:
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
    category: Optional[Category] = typer.Option(None, "--category", "-c", help="Filter by category"),
    difficulty: Optional[Difficulty] = typer.Option(None, "--difficulty", "-d", help="Filter by difficulty"),
    retired: bool = typer.Option(False, "--retired", help="Show retired challenges"),
    unsolved: bool = typer.Option(False, "--unsolved", "-u", help="Show only unsolved"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """List available challenges."""
    try:
        if retired:
            data = api_get("/challenge/list/retired")
        else:
            data = api_get("/challenge/list")

        challenges = data.get("challenges", data.get("data", []))

        # The list endpoint doesn't include category_name, so build a map
        # from challenge_category_id -> name using the categories endpoint
        if not challenges or "category_name" not in challenges[0]:
            try:
                cats_data = api_get("/challenge/categories/list")
                cat_map = {c["id"]: c["name"] for c in cats_data.get("info", [])}
                for c in challenges:
                    c["category_name"] = cat_map.get(c.get("challenge_category_id"), "Unknown")
            except HTBError:
                pass

        if raw:
            print_json(data)
            return

        # Apply filters
        if category:
            challenges = [c for c in challenges if c.get("category_name", "").lower() == category.value]

        if difficulty:
            challenges = [c for c in challenges if c.get("difficulty", "").lower() == difficulty.value.replace("_", " ")]

        if unsolved:
            challenges = [c for c in challenges if not c.get("isCompleted") and not c.get("isSolved") and not c.get("solved")]

        title = "Retired Challenges" if retired else "Active Challenges"
        print_challenges(challenges, title)

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
        data = api_post("/challenge/start", {"challenge_id": challenge_id})

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
    name: str = typer.Argument(..., help="Challenge name or ID"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Stop a running challenge."""
    try:
        challenge_id = _resolve_challenge_id(name)
        data = api_post("/challenge/stop", {"challenge_id": challenge_id})

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
        content = api_download_bytes(f"/challenge/download/{challenge_id}")

        # Get challenge name for filename if not specified
        if output is None:
            try:
                info_data = api_get(f"/challenge/info/{challenge_id}")
                challenge_name = info_data.get("challenge", {}).get("name", f"challenge_{challenge_id}")
            except Exception:
                challenge_name = f"challenge_{challenge_id}"
            output = Path(f"{challenge_name}.zip")

        output.write_bytes(content)
        print_success(f"Downloaded to: {output}")

    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("own")
def own(
    flag: str = typer.Argument(..., help="Flag to submit"),
    name: Optional[str] = typer.Option(None, "--challenge", "-c", help="Challenge name or ID (auto-detects if docker running)"),
    difficulty: int = typer.Option(0, "--difficulty", "-d", help="Difficulty rating (0-100)"),
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
            "id": challenge_id,
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

        # Enrich with category names
        try:
            cats_data = api_get("/challenge/categories/list")
            cat_map = {c["id"]: c["name"] for c in cats_data.get("info", [])}
            for c in running:
                c["category_name"] = cat_map.get(c.get("challenge_category_id"), "Unknown")
        except HTBError:
            pass

        for c in running:
            print_challenge(c)

    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)
