"""
Auth/token management commands.

Commands:
- htb auth set       - Store API token (keyring preferred)
- htb auth show      - Show token source (no token reveal)
- htb auth unset     - Remove stored token
- htb auth status    - Validate token and show user info
"""

import typer

from ..client import HTBError, api_get
from ..config import get_token_source, resolve_token, set_token, unset_token
from ..formatters import print_error, print_key_value, print_success, print_warning

app = typer.Typer(help="Auth/token management")


@app.command("set")
def set_token_cmd(
    token: str = typer.Option(
        ...,
        "--token",
        "-t",
        prompt=True,
        hide_input=True,
        confirmation_prompt=True,
        help="HTB API token",
    ),
):
    """Store API token securely (keyring preferred)."""
    try:
        dest = set_token(token)
        if dest == "keyring":
            print_success("Token saved to OS keyring")
        else:
            print_success("Token saved to config file")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("show")
def show_token_source():
    """Show token source without revealing the token."""
    source = get_token_source()
    if not source:
        print_warning("No token found")
        raise typer.Exit(1)

    # Show masked token length + last 4 for confidence if possible
    try:
        token, _ = resolve_token()
        masked = f"{'*' * max(len(token) - 4, 0)}{token[-4:]}" if token else "N/A"
    except Exception:
        masked = "N/A"

    info = {
        "Source": source,
        "Token": masked,
    }
    print_key_value(info, "HTB Token")


@app.command("unset")
def unset_token_cmd():
    """Remove stored token from keyring and file."""
    removed = unset_token()
    if removed.get("keyring") or removed.get("file"):
        print_success("Token removed")
    else:
        print_warning("No stored token found")


@app.command("status")
def status():
    """Validate token and show current user info."""
    try:
        data = api_get("/user/info")
        info = data.get("info", {})

        uid = info.get("id")
        profile = {}
        if uid:
            try:
                prof_data = api_get(f"/user/profile/basic/{uid}")
                profile = prof_data.get("profile", {})
            except Exception:
                profile = {}

        user_info = {
            "ID": info.get("id"),
            "Username": info.get("name"),
            "Rank": profile.get("rank", info.get("rank")),
            "Ranking": f"#{profile.get('ranking', info.get('ranking'))}",
            "Rank Progress": f"{profile.get('current_rank_progress', 0):.1f}%" if profile.get("current_rank_progress") is not None else None,
            "Next Rank": profile.get("next_rank"),
            "Points": profile.get("userStats", {}).get("points") or profile.get("points"),
            "Respects": profile.get("respects", info.get("respects")),
            "Country": profile.get("country_name"),
            "Team": profile.get("team", {}).get("name") if profile.get("team") else None,
            "Joined": str(profile.get("joined_date", ""))[:10] if profile.get("joined_date") else None,
        }
        user_info = {k: v for k, v in user_info.items() if v is not None}
        print_key_value(user_info, f"User: {profile.get('name', info.get('name', 'Unknown'))}")
    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)
