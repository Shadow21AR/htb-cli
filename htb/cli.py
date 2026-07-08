"""
HTB CLI - Command Line Interface for Hack The Box.

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

    htb dashboard favorites       Show favorite/owned items
    htb dashboard inprogress      Show in-progress items
    htb dashboard recommended     Show recommended items

    htb profile basic ID          View user's profile
    htb profile badges ID         View user's badges
    htb profile activity ID       View user's recent activity
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

    htb health                     Check HTB service health (no login required)

All commands support --raw/-r for JSON output.
"""


import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .client import HTBError
from .commands import auth, challenges, dashboard, fortresses, health, machines, profile, pwnbox, rankings, season, sherlocks, teams, test as test_cmd, tracks, vpn
from .formatters import print_error, print_json, print_key_value, sanitize_text

console = Console()

HTB_ART = """\
[cyan]██╗  ██╗████████╗██████╗ 
██║  ██║╚══██╔══╝██╔══██╗
███████║   ██║   ██████╔╝
██╔══██║   ██║   ██╔══██╗
██║  ██║   ██║   ██████╔╝
╚═╝  ╚═╝   ╚═╝   ╚═════╝[/cyan]"""

# Create main app
app = typer.Typer(
    name="htb",
    help="CLI for Hack The Box",
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
app.add_typer(health.app, name="health")
app.add_typer(test_cmd.app, name="test")


@app.command("status")
def status(
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Quick overview: user, connection, and active machine."""
    from .client import api_get, api_get_experience, api_get_v5

    try:
        user_data = api_get("/user/info")
        conn_data = api_get_v5("/connections")
        machine_data = api_get_v5("/virtual_machine/active")

        if raw:
            print_json({"user": user_data, "connection": conn_data, "machine": machine_data})
            return

        # ── User panel ──
        info = user_data.get("info", {})
        uid = info.get("id")
        account_id = info.get("account_id")
        profile = {}
        experience = {}
        if uid:
            try:
                prof_data = api_get(f"/user/profile/basic/{uid}")
                profile = prof_data.get("profile", {})
            except Exception:
                profile = {}

        if account_id:
            try:
                experience = api_get_experience(f"/account/{account_id}")
            except Exception:
                experience = {}

        points = profile.get("userStats", {}).get("points") or profile.get("points")
        level = experience.get("level")
        level_title = experience.get("levelTitle")
        xp = experience.get("totalExperiencePoints")
        streak = experience.get("streakData", {}).get("counter")
        lvl_str = None
        if level is not None:
            lvl_str = f"{level}"
            if level_title:
                lvl_str += f" {level_title}"
        xp_str = f"{xp:,}" if xp else None
        streak_str = f"{streak}w" if streak else None

        user_parts = {
            "Name": profile.get("name", info.get("name")),
            "Rank": profile.get("rank", info.get("rank")),
            "Points": points,
            "Ranking": f"#{profile.get('ranking', info.get('ranking'))}",
            "Level": lvl_str,
            "XP": xp_str,
            "Streak": streak_str,
            "Rank Progress": f"{profile.get('current_rank_progress', 0):.1f}%" if profile.get("current_rank_progress") is not None else None,
            "Next Rank": profile.get("next_rank"),
            "Respects": profile.get("respects", info.get("respects")),
            "Country": profile.get("country_name"),
            "Team": profile.get("team", {}).get("name") if profile.get("team") else None,
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
    """Show current user info with style."""
    from .client import api_get, api_get_experience

    try:
        data = api_get("/user/info")
        info = data.get("info", {})

        uid = info.get("id")
        account_id = info.get("account_id")
        profile = {}
        experience = {}
        if uid:
            try:
                prof_data = api_get(f"/user/profile/basic/{uid}")
                profile = prof_data.get("profile", {})
            except Exception:
                profile = {}

        if account_id:
            try:
                experience = api_get_experience(f"/account/{account_id}")
            except Exception:
                experience = {}

        if raw:
            print_json({"user": data, "profile": profile, "experience": experience})
            return

        name = profile.get("name", info.get("name", "Unknown"))
        rank = profile.get("rank", info.get("rank"))
        ranking = profile.get("ranking", info.get("ranking"))
        rank_id = profile.get("rank_id", info.get("rank_id"))
        points = profile.get("userStats", {}).get("points") or profile.get("points")
        team_name = profile.get("team", {}).get("name") if profile.get("team") else None
        joined = str(profile.get("joined_date", ""))[:10] if profile.get("joined_date") else None

        level = experience.get("level")
        level_title = experience.get("levelTitle")
        xp = experience.get("totalExperiencePoints")
        streak_data = experience.get("streakData", {})
        streak_count = streak_data.get("counter")
        max_streak = streak_data.get("maxStreak")
        streak_danger = streak_data.get("inDanger")

        # HTB ASCII art header
        console.print(HTB_ART)
        console.print(f"[bold]          Welcome, [green]{sanitize_text(name)}[/green]![/bold]")
        console.print()

        from rich.progress import BarColumn, Progress, TextColumn

        layout = Table.grid(padding=(0, 2))
        layout.add_column(ratio=1)

        def ln(*parts):
            layout.add_row("  ".join(str(p) for p in parts if p is not None))

        # ── Header line ──
        header = f"[bold green]>[/bold green] [bold]{sanitize_text(name)}[/bold]"
        if rank:
            header += f"  [dim]│[/dim]  [green]{rank}[/green]"
        if ranking:
            header += f"  [dim]│[/dim]  [bold]#{ranking}[/bold]"
        ln(header)

        # ── Info grid (3 per row) ──
        def group(*pairs):
            parts = []
            for label, val in pairs:
                if val is not None:
                    parts.append(f"[dim]{label}:[/dim] [bold]{val}[/bold]")
            if parts:
                ln("  ".join(parts))

        group(("ID", info.get("id")), ("Pts", f"{points:,}" if points else None), ("VIP", "[green]Y[/green]" if profile.get("isVip") else "[dim]N[/dim]"))
        group(("Ctry", profile.get("country_name")), ("Team", team_name), ("Since", joined))

        # Level / XP / Streak on one row
        lvl_str = None
        if level is not None:
            lvl_str = f"{level}"
            if level_title:
                lvl_str += f" [dim]{level_title}[/dim]"
        xp_str = f"{xp:,}" if xp is not None else None
        streak_str = None
        if streak_count is not None:
            streak_str = f"{streak_count}w"
            if streak_danger:
                streak_str += " [yellow]⚠[/yellow]"
        group(("Lvl", lvl_str), ("XP", xp_str), ("Strk", streak_str))

        # ── Rank progress ──
        progress_pct = profile.get("current_rank_progress")
        next_rank = profile.get("next_rank")
        if progress_pct is not None and next_rank:
            pct = float(progress_pct)
            bar = Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(bar_width=None),
                TextColumn("[progress.percentage]{task.percentage:>3.1f}%"),
            )
            bar.add_task(f"[green]{next_rank}[/green]", total=100, completed=int(pct))
            layout.add_row("")
            layout.add_row(bar)

        # ── Level XP progress ──
        lvl_xp = experience.get("levelExperiencePoints")
        lvl_xp_remaining = experience.get("experienceUntilNextLevel")
        if lvl_xp is not None and lvl_xp_remaining is not None:
            total = lvl_xp + lvl_xp_remaining
            if total > 0:
                bar = Progress(
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(bar_width=None),
                    TextColumn("[progress.percentage]{task.percentage:>3.1f}%"),
                )
                bar.add_task(f"[green]XP to next level[/green]  [dim]({lvl_xp}/{total})[/dim]", total=total, completed=lvl_xp)
                layout.add_row("")
                layout.add_row(bar)

        # ── Social ──
        social = {}
        if profile.get("github"):
            social["GitHub"] = profile["github"]
        if profile.get("twitter"):
            social["Twitter"] = profile["twitter"]
        if social:
            layout.add_row("")
            for k, v in social.items():
                ln(f"[dim]{k}:[/dim] {v}")

        console.print(Panel(layout, box=box.HEAVY))

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
    """HTB CLI - Hack The Box from your terminal."""
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())
        raise typer.Exit()


if __name__ == "__main__":
    app()
