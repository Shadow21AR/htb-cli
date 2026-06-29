"""
Pwnbox commands.

Commands:
- htb pwnbox status      - Show Pwnbox status
- htb pwnbox start       - Start Pwnbox
- htb pwnbox stop        - Stop Pwnbox
- htb pwnbox usage       - Show usage stats
"""

from typing import Optional

import typer

from ..client import HTBError, api_get, api_post
from ..formatters import console, print_error, print_json, print_key_value, print_success, print_warning

app = typer.Typer(help="Pwnbox management")


@app.command("status")
def status(
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Show current Pwnbox status."""
    try:
        data = api_get("/v4/pwnbox/status")
        if raw:
            print_json(data)
        elif "message" in data:
            console.print(f"[yellow]{data['message']}[/yellow]")
        else:
            p = data.get("data", data)
            info = {
                "Hostname": p.get("hostname"),
                "Status": p.get("status"),
                "Location": p.get("location"),
                "Username": p.get("username"),
                "VNC Password": p.get("vnc_password"),
                "Life Remaining": f"{p.get('life_remaining', 0)}m" if p.get("life_remaining") is not None else None,
                "Expires At": str(p.get("expires_at", ""))[:19] if p.get("expires_at") else None,
                "Proxy": p.get("proxy_url"),
                "Spectate URL": p.get("spectate_url"),
            }
            info = {k: v for k, v in info.items() if v is not None}
            print_key_value(info, "Pwnbox Status")
    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("start")
def start(
    location: str = typer.Option("us-east", "--location", "-l", help="Pwnbox region"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Start Pwnbox instance."""
    try:
        data = api_post("/v4/pwnbox/start", {"location": location})
        if raw:
            print_json(data)
        else:
            p = data.get("data", data)
            hostname = p.get("hostname")
            if hostname:
                print_success(f"Pwnbox started: {hostname}")
            else:
                print_success(data.get("message", "Pwnbox started"))
    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("stop")
def stop(
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Stop Pwnbox instance."""
    try:
        data = api_post("/v4/pwnbox/terminate", {})
        if raw:
            print_json(data)
        else:
            print_success(data.get("message", "Pwnbox stopped"))
    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("usage")
def usage(
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Show Pwnbox usage statistics."""
    try:
        data = api_get("/v4/pwnbox/usage")
        if raw:
            print_json(data)
        else:
            info = {
                "Allowed": data.get("allowed"),
                "Remaining": data.get("remaining"),
                "Used": data.get("used"),
                "Total Sessions": data.get("total", data.get("sessions")),
                "Active Minutes": data.get("active_minutes", 0),
            }
            info = {k: v for k, v in info.items() if v is not None}
            print_key_value(info, "Pwnbox Usage")
    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)
