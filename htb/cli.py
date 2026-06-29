"""
HTB CLI - Command Line Interface for Hack The Box Labs.

Usage:
    htb status                    Quick status overview
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

All commands support --raw/-r for JSON output.
"""


import typer
from rich.console import Console

from .client import HTBError
from .commands import auth, challenges, machines, season, sherlocks, test as test_cmd, vpn
from .formatters import print_error, print_json, print_key_value, sanitize_text

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
app.add_typer(auth.app, name="auth")
app.add_typer(test_cmd.app, name="test")


@app.command("status")
def status(
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Quick status: show active machine and connection."""
    from .client import api_get

    try:
        # Get connection status
        conn = api_get("/connection/status")

        # Get active machine
        machine = api_get("/machine/active")

        if raw:
            print_json({"connection": conn, "machine": machine})
            return

        # Display connection info
        if conn:
            conn_data = conn[0] if isinstance(conn, list) and conn else conn
            if conn_data:
                console.print("[bold cyan]Connection[/bold cyan]")
                server = conn_data.get("server", {})
                if server:
                    console.print(f"  Server: {sanitize_text(server.get('friendly_name', 'Unknown'))}")
                ip = conn_data.get("connection", {}).get("ip4")
                if ip:
                    console.print(f"  IP: {sanitize_text(ip)}")
                console.print()

        # Display machine info
        machine_info = machine.get("info")
        if machine_info:
            console.print("[bold cyan]Active Machine[/bold cyan]")
            console.print(f"  Name: {sanitize_text(machine_info.get('name'))}")
            console.print(f"  OS: {sanitize_text(machine_info.get('os'))}")
            console.print(f"  IP: {sanitize_text(machine_info.get('ip', 'Not assigned'))}")
            console.print(f"  Difficulty: {sanitize_text(machine_info.get('difficultyText'))}")
            desc = machine_info.get("info_status") or machine_info.get("synopsis")
            if desc:
                console.print(f"  Description: {sanitize_text(desc)}")
        else:
            console.print("[dim]No active machine[/dim]")

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

        # Display machines
        machines_list = data.get("machines", [])
        if machines_list:
            table = create_table(["ID", "Name"], "Machines")
            for m in machines_list[:10]:
                table.add_row(
                    str(m.get("id", "?")),
                    sanitize_text(m.get("value", m.get("name", "?"))),
                )
            console.print(table)
            console.print()

        # Display challenges
        challs = data.get("challenges", [])
        if challs:
            table = create_table(["ID", "Name", "Category"], "Challenges")
            for c in challs[:10]:
                table.add_row(
                    str(c.get("id", "?")),
                    sanitize_text(c.get("value", c.get("name", "?"))),
                    sanitize_text(c.get("category_name", "?")),
                )
            console.print(table)
            console.print()

        # Display users
        users = data.get("users", [])
        if users:
            table = create_table(["ID", "Username"], "Users")
            for u in users[:10]:
                table.add_row(
                    str(u.get("id", "?")),
                    sanitize_text(u.get("value", u.get("name", "?"))),
                )
            console.print(table)

        if not machines_list and not challs and not users:
            console.print("[dim]No results found[/dim]")

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
