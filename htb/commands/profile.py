"""
Profile commands.

Commands:
- htb profile basic <id>     - View user's profile
- htb profile badges <id>    - View user's badges
- htb profile activity <id>  - View user's recent activity
- htb profile content <id>   - View user's solves/owns
"""

from typing import Optional

import typer

from ..client import HTBError, api_get
from ..formatters import (
    console,
    create_table,
    print_error,
    print_json,
    print_key_value,
    sanitize_text,
)

app = typer.Typer(help="User profile")


@app.command("basic")
def basic(
    user_id: int = typer.Argument(..., help="User ID"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """View a user's profile."""
    try:
        data = api_get(f"/v4/user/profile/basic/{user_id}")
        if raw:
            print_json(data)
            return

        profile = data.get("profile", {})
        if not profile:
            print_error("User not found")
            raise typer.Exit(1)

        team = profile.get("team", {})
        info = {
            "Name": profile.get("name"),
            "Rank": profile.get("rank"),
            "Ranking": profile.get("ranking"),
            "Points": profile.get("points"),
            "User Owns": profile.get("user_owns"),
            "Root Owns": profile.get("system_owns"),
            "Respects": profile.get("respects"),
            "Team": team.get("name"),
            "Country": profile.get("country_name"),
            "Joined": str(profile.get("joined_date", ""))[:10] if profile.get("joined_date") else None,
        }
        info = {k: v for k, v in info.items() if v is not None}
        print_key_value(info, f"User: {profile.get('name', user_id)}")

    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("badges")
def badges(
    user_id: int = typer.Argument(..., help="User ID"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """View a user's badges."""
    try:
        data = api_get(f"/v4/user/profile/badges/{user_id}")
        if raw:
            print_json(data)
            return

        badges_list = data.get("badges", [])
        if not badges_list:
            console.print("[dim]No badges[/dim]")
            return

        table = create_table(["Badge", "Description"], f"Badges ({len(badges_list)})")
        for b in badges_list:
            table.add_row(
                sanitize_text(b.get("name", "?")),
                sanitize_text(b.get("description", "")),
            )
        console.print(table)

    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("activity")
def activity(
    user_id: int = typer.Argument(..., help="User ID"),
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """View a user's recent activity (solves)."""
    try:
        data = api_get(f"/v5/user/profile/activity/{user_id}", {"page": page})
        if raw:
            print_json(data)
            return

        items = data.get("data", [])
        if not items:
            console.print("[dim]No activity found[/dim]")
            return

        table = create_table(["Date", "Type", "Name", "Points"], "Recent Activity")
        for item in items:
            table.add_row(
                str(item.get("ownDate", item.get("date", "?")))[:10],
                sanitize_text(item.get("type", "?")),
                sanitize_text(item.get("name", "?")),
                str(item.get("points", "?")),
            )
        console.print(table)

        meta = data.get("meta", {})
        if meta:
            current = meta.get("page", page)
            last = meta.get("lastPage", "?")
            console.print(f"\n[dim]Page {current}/{last}[/dim]")

    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("content")
def content(
    user_id: int = typer.Argument(..., help="User ID"),
    type: str = typer.Option("machine", "--type", "-t", help="Content type: machine, challenge, sherlock"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """View a user's solves/owns by content type."""
    try:
        data = api_get(f"/v5/user/profile/content/{user_id}", {"type": type})
        if raw:
            print_json(data)
            return

        items = data.get("data", [])
        if not items:
            console.print("[dim]No content found[/dim]")
            return

        if type == "machine":
            table = create_table(["ID", "Name", "OS", "Difficulty", "Rating", "User", "Root"], f"Machines ({len(items)})")
            for item in items:
                table.add_row(
                    str(item.get("id", "?")),
                    sanitize_text(item.get("name", "?")),
                    sanitize_text(item.get("os", "?")),
                    sanitize_text(item.get("difficulty", "?")),
                    str(item.get("starRating", "?")),
                    str(item.get("userOwnCount", "?")),
                    str(item.get("rootOwnCount", "?")),
                )
        else:
            table = create_table(["ID", "Name", "Difficulty"], f"{type.title()}s ({len(items)})")
            for item in items:
                table.add_row(
                    str(item.get("id", "?")),
                    sanitize_text(item.get("name", "?")),
                    sanitize_text(item.get("difficulty", "?")),
                )
        console.print(table)

    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)
