"""
HTB CLI - Command Line Interface for Hack The Box Labs.

Usage:
    htb status                    Overview: user, connection, active machine
    htb whoami                    Show current user info
    htb search QUERY              Global search

    htb machine list              List machines (--state, --todo, etc.)
    htb machine spawn NAME        Spawn a machine
    htb machine own FLAG          Submit flag
    htb machine stop              Terminate active machine
    htb machine reset             Reset active machine
    htb machine active            Show active machine
    htb machine info NAME         Get machine details
    htb machine writeup NAME      Get writeup URL
    htb machine add-todo NAME     Toggle todo
    htb machine achievement NAME  Print achievement URL

    htb challenge list            List challenges
    htb challenge info NAME       Get challenge details
    htb challenge start NAME      Start challenge docker
    htb challenge stop [NAME]     Stop running docker
    htb challenge own FLAG        Submit flag
    htb challenge download NAME   Download files
    htb challenge active          Show running docker
    htb challenge categories      List categories

    htb sherlock list             List sherlocks
    htb sherlock info NAME        Get sherlock details
    htb sherlock tasks NAME       Show tasks/questions
    htb sherlock download NAME    Download files
    htb sherlock own NAME FLAG    Submit answer
    htb sherlock categories       List categories
    htb sherlock progress NAME    Show progress
    htb sherlock writeup NAME     Get community writeup
    htb sherlock official-writeup NAME  Get official writeup URL

    htb vpn status                Show VPN status
    htb vpn servers               List VPN servers
    htb vpn connections           Show all active connections
    htb vpn switch ID             Switch VPN server
    htb vpn download ID           Download VPN config

    htb season list               List seasons
    htb season machines           Show season machines
    htb season active-machines    Show active season machines
    htb season own FLAG           Submit arena flag
    htb season rank [ID]          Show season ranking
    htb season leaderboard [ID]   Show season leaderboard

    htb season leaderboard [ID]   Show season leaderboard

    htb dashboard favorites       Show favorite/owned items
    htb dashboard inprogress      Show in-progress items
    htb dashboard recommended     Show recommended items

    htb profile basic ID          View user's profile
    htb profile badges ID         View user's badges
    htb profile activity ID       View user's recent activity
    htb profile content ID        View user's solves/owns

    htb profile content ID        View user's solves/owns

    htb pwnbox status             Show Pwnbox status
    htb pwnbox start              Start Pwnbox
    htb pwnbox stop               Stop Pwnbox
    htb pwnbox usage              Show usage stats

    htb fortress list             List fortresses
    htb fortress info ID          Get fortress details
    htb fortress flags ID         Show fortress flags
    htb fortress own ID FLAG      Submit flag
    htb fortress reset ID         Vote to reset

    htb track list                List tracks
    htb track info ID             Get track details
    htb track enroll ID           Enroll in a track
    htb track like ID             Like a track

    htb ranking users             Top users
    htb ranking teams             Top teams
    htb ranking countries         Top countries
    htb ranking universities      Top universities
    htb ranking country-members CODE  Country members

    htb team info ID               Get team profile
    htb team members ID            List team members
    htb team activity ID           Show recent team activity

All commands support --raw/-r for JSON output.
"""


import typer
from rich.console import Console

from .client import HTBError
from .commands import auth, challenges, dashboard, fortresses, machines, profile, pwnbox, rankings, season, sherlocks, teams, test as test_cmd, tracks, vpn
from .formatters import print_error, print_json, print_key_value, sanitize_text
from rich import box
from rich.console import Console
from rich.panel import Panel

console = Console()

# Create main app
app = typer.Typer(
    name="htb",
    help="CLI for Hack The Box Labs API",
    no_args_is_help=True,
)

# Add command groups
app.add_typer(vpn.app, name="vpn")
app.add_typer(machines.app, name="machine")
app.add_typer(season.app, name="season")
app.add_typer(challenges.app, name="challenge")
app.add_typer(sherlocks.app, name="sherlock")
app.add_typer(dashboard.app, name="dashboard")
app.add_typer(profile.app, name="profile")
app.add_typer(pwnbox.app, name="pwnbox")
app.add_typer(fortresses.app, name="fortress")
app.add_typer(tracks.app, name="track")
app.add_typer(rankings.app, name="ranking")
app.add_typer(teams.app, name="team")
app.add_typer(auth.app, name="auth")
app.add_typer(test_cmd.app, name="test")


@app.command("status")
def status(
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Quick overview: user, connection, and active machine."""
    from .client import api_get

    try:
        user_data = api_get("/user/info")
        conn_data = api_get("/v5/connections")
        machine_data = api_get("/v5/virtual_machine/active")

        if raw:
            print_json({"user": user_data, "connection": conn_data, "machine": machine_data})
            return

        # ── User panel ──
        info = user_data.get("info", {})
        user_parts = {
            "Name": info.get("name"),
            "Rank": info.get("rank"),
            "Points": info.get("points"),
            "Respects": info.get("respects"),
        }
        user_parts = {k: v for k, v in user_parts.items() if v is not None}
        console.print(Panel(
            "\n".join(f"[cyan]{k}:[/cyan] {v}" for k, v in user_parts.items()),
            title="User",
            box=box.ROUNDED,
        ))

        # ── Connection panel ──
        conns = conn_data.get("data", [])
        if conns:
            connected = [c for c in conns if isinstance(c.get("assigned_server"), dict)]
            if connected:
                c = connected[0]
                srv = c.get("assigned_server", {})
                conn_parts = {
                    "Server": srv.get("friendly_name"),
                    "Location": srv.get("location"),
                    "Type": c.get("location_type_friendly"),
                }
            else:
                conn_parts = {"Status": "Not connected"}
            console.print(Panel(
                "\n".join(f"[cyan]{k}:[/cyan] {sanitize_text(v)}" for k, v in conn_parts.items() if v),
                title="Connection",
                box=box.ROUNDED,
            ))
        else:
            console.print(Panel("[dim]No connection data[/dim]", title="Connection", box=box.ROUNDED))

        # ── Active Machine panel ──
        mm = machine_data.get("info")
        if mm:
            machine_parts = {
                "Name": mm.get("name"),
                "OS": mm.get("os"),
                "IP": mm.get("ip", "Not assigned"),
                "Difficulty": mm.get("difficultyText"),
            }
            console.print(Panel(
                "\n".join(f"[cyan]{k}:[/cyan] {sanitize_text(v)}" for k, v in machine_parts.items() if v),
                title="Active Machine",
                box=box.ROUNDED,
            ))
        else:
            console.print(Panel("[dim]No active machine[/dim]", title="Active Machine", box=box.ROUNDED))

    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("whoami")
def whoami(
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Show current user info."""
    from .client import api_get

    try:
        data = api_get("/user/info")

        if raw:
            print_json(data)
            return

        info = data.get("info", {})
        user_info = {
            "ID": info.get("id"),
            "Username": info.get("name"),
            "Rank": info.get("rank"),
            "Points": info.get("points"),
            "Ranking": info.get("ranking"),
            "Team": info.get("team", {}).get("name") if info.get("team") else None,
        }

        user_info = {k: v for k, v in user_info.items() if v is not None}
        print_key_value(user_info, f"User: {info.get('name', 'Unknown')}")

    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("search")
def search(
    query: str = typer.Argument(..., help="Search query"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Search for machines, challenges, and users."""
    from .client import api_get
    from .formatters import create_table

    try:
        data = api_get("/search/fetch", {"query": query})

        if raw:
            print_json(data)
            return

        machines_list = data.get("machines", [])
        challs = data.get("challenges", [])
        users = data.get("users", [])

        if not machines_list and not challs and not users:
            console.print("[dim]No results found[/dim]")
            return

        table = create_table(["Type", "ID", "Name"], f"Search: {query}")
        for m in machines_list[:10]:
            table.add_row("Machine", str(m.get("id", "?")), sanitize_text(m.get("value", m.get("name", "?"))))
        for c in challs[:10]:
            table.add_row("Challenge", str(c.get("id", "?")), sanitize_text(c.get("value", c.get("name", "?"))))
        for u in users[:10]:
            table.add_row("User", str(u.get("id", "?")), sanitize_text(u.get("value", u.get("name", "?"))))
        console.print(table)

    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)


def version_callback(value: bool):
    if value:
        from . import __version__
        console.print(f"htb-cli version {__version__}")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-v", help="Show version", callback=version_callback, is_eager=True),
):
    """HTB CLI - Hack The Box Labs from your terminal."""
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())
        raise typer.Exit()


if __name__ == "__main__":
    app()
