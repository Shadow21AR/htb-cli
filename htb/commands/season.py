"""
Season/Arena commands.

Commands:
- htb season list       - List seasons
- htb season machines   - Show current season machines
- htb season own        - Submit flag for season points
- htb season rank       - Show your season ranking
"""

from typing import Optional

import typer

from ..client import HTBError, api_get, api_post
from ..formatters import (
    console,
    create_table,
    print_error,
    print_flag_result,
    print_json,
    print_key_value,
    print_machines,
    print_warning,
    sanitize_text,
)

app = typer.Typer(help="Season/Arena management")


@app.command("list")
def list_seasons(
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """List all seasons."""
    try:
        data = api_get("/season/list")

        if raw:
            print_json(data)
            return

        seasons = data.get("data", [])
        if not seasons:
            print_warning("No seasons found")
            return

        table = create_table(["ID", "Name", "Status", "Start", "End"], "Seasons")

        for s in seasons:
            status = "Active" if s.get("active") else "Ended"
            table.add_row(
                str(s.get("id", "?")),
                sanitize_text(s.get("name", "?")),
                status,
                s.get("start_date", "?")[:10] if s.get("start_date") else "?",
                s.get("end_date", "?")[:10] if s.get("end_date") else "?",
            )

        console.print(table)

    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("machines")
def machines(
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Show current season machines."""
    try:
        data = api_get("/season/machines")

        if raw:
            print_json(data)
        else:
            machines = data.get("data", [])
            print_machines(machines, "Season Machines")

    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("active")
def active_machines(
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Show active season machines (currently playable)."""
    try:
        data = api_get("/season/machine/active")

        if raw:
            print_json(data)
        else:
            machines = data.get("data", [])
            print_machines(machines, "Active Season Machines")

    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("own")
def own(
    flag: str = typer.Argument(..., help="Flag to submit"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Submit a flag for season points (arena)."""
    try:
        # Get active machine ID first
        active_data = api_get("/machine/active")
        info = active_data.get("info")

        if not info:
            print_error("No active machine")
            raise typer.Exit(1)

        machine_id = info.get("id")

        # Use arena endpoint for seasonal points
        data = api_post("/arena/own", {
            "id": machine_id,
            "flag": flag,
        })

        if raw:
            print_json(data)
        else:
            print_flag_result(data)

    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("rank")
def rank(
    season_id: Optional[int] = typer.Argument(None, help="Season ID (default: current)"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Show your ranking in a season."""
    try:
        # Get user info to get user ID
        user_data = api_get("/user/info")
        user_id = user_data.get("info", {}).get("id")

        if not user_id:
            print_error("Could not get user info")
            raise typer.Exit(1)

        # If no season_id, get current season
        if season_id is None:
            seasons = api_get("/season/list")
            for s in seasons.get("data", []):
                if s.get("active"):
                    season_id = s.get("id")
                    break

        if season_id is None:
            print_error("No active season found")
            raise typer.Exit(1)

        data = api_get(f"/season/user/rank/{season_id}")

        if raw:
            print_json(data)
            return

        rank_data = data.get("data", {})
        rank_val = rank_data.get("rank")
        total = rank_data.get("total_ranks")
        rank_str = f"{rank_val}/{total}" if rank_val and total else str(rank_val or "Unranked")
        flags = rank_data.get("total_season_flags", {})
        info = {
            "Season": season_id,
            "League": rank_data.get("league", "N/A"),
            "Rank": rank_str,
            "Points": rank_data.get("total_season_points", rank_data.get("points", 0)),
            "User Owns": rank_data.get("user_owns", 0),
            "Root Owns": rank_data.get("root_owns", 0),
            "Flags": f"{flags.get('obtained', 0)}/{flags.get('total', 0)}" if flags else "0",
        }

        print_key_value(info, "Season Ranking")

    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("leaderboard")
def leaderboard(
    season_id: Optional[int] = typer.Argument(None, help="Season ID (default: current)"),
    limit: int = typer.Option(10, "--limit", "-l", help="Number of entries to show"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Show season leaderboard."""
    try:
        # If no season_id, get current season
        if season_id is None:
            seasons = api_get("/season/list")
            for s in seasons.get("data", []):
                if s.get("active"):
                    season_id = s.get("id")
                    break

        if season_id is None:
            print_error("No active season found")
            raise typer.Exit(1)

        data = api_get(f"/season/players/leaderboard/top/{season_id}")

        if raw:
            print_json(data)
            return

        entries = data.get("data", [])[:limit]
        if not entries:
            print_warning("No leaderboard entries")
            return

        table = create_table(["Rank", "League", "User", "Points", "Owns"], f"Season {season_id} Leaderboard")

        for entry in entries:
            owns = entry.get("user_owns", 0) + entry.get("root_owns", 0)
            table.add_row(
                str(entry.get("rank", "?")),
                sanitize_text(entry.get("league_rank", "?")),
                sanitize_text(entry.get("name", entry.get("username", "?"))),
                str(entry.get("points", 0)),
                str(owns),
            )

        console.print(table)

    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)
