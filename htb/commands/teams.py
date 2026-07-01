"""Team commands.

Commands:
- htb team info        - Get team profile
- htb team members     - List team members
- htb team activity    - Show recent team activity
"""

import typer

from ..client import HTBError, api_get
from ..formatters import print_error, print_json, print_team, print_team_activity, print_team_members

app = typer.Typer(help="Team management")


@app.command("info")
def info(
    team_id: int = typer.Argument(..., help="Team ID"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Get team profile."""
    try:
        data = api_get(f"/team/info/{team_id}")
        if raw:
            print_json(data)
            return
        print_team(data)
    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("members")
def members(
    team_id: int = typer.Argument(..., help="Team ID"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """List team members."""
    try:
        data = api_get(f"/team/members/{team_id}")
        if raw:
            print_json(data)
            return
        members_list = data if isinstance(data, list) else data.get("data", data.get("members", []))
        print_team_members(members_list, team_id)
    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("activity")
def activity(
    team_id: int = typer.Argument(..., help="Team ID"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Show recent team activity."""
    try:
        data = api_get(f"/team/activity/{team_id}")
        if raw:
            print_json(data)
            return
        activity_list = data if isinstance(data, list) else data.get("data", [])
        print_team_activity(activity_list, team_id)
    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)
