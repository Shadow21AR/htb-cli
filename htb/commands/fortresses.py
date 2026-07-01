"""Fortress commands.

Commands:
- htb fortress list       - List fortresses
- htb fortress info       - Get fortress details
- htb fortress flags      - Show fortress flags
- htb fortress own        - Submit flag
- htb fortress reset      - Vote to reset fortress
"""

from typing import Optional

import typer

from ..client import HTBError, api_get, api_post
from ..formatters import (
    print_error,
    print_fortress,
    print_fortresses,
    print_json,
    print_key_value,
    print_success,
)

app = typer.Typer(help="Fortress management")


@app.command("list")
def list_fortresses(
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """List all fortresses."""
    try:
        data = api_get("/fortresses")
        if raw:
            print_json(data)
            return

        fortresses = data.get("data", [])
        print_fortresses(fortresses)
    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("info")
def info(
    fortress_id: int = typer.Argument(..., help="Fortress ID"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Get detailed information about a fortress."""
    try:
        data = api_get(f"/fortress/{fortress_id}")
        if raw:
            print_json(data)
            return

        fortress = data.get("data", data)
        print_fortress(fortress)
    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("flags")
def flags(
    fortress_id: int = typer.Argument(..., help="Fortress ID"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Show flags for a fortress."""
    try:
        data = api_get(f"/fortress/{fortress_id}/flags")
        if raw:
            print_json(data)
            return

        flag_list = data.get("data", [])
        if not flag_list:
            from ..formatters import console, print_warning
            print_warning("No flags found for this fortress")
            return

        from ..formatters import create_table
        table = create_table(["ID", "Title", "Points", "Owned"], f"Fortress {fortress_id} Flags")
        for f in flag_list:
            owned = "[green]✓[/green]" if f.get("owned") else "[dim]○[/dim]"
            table.add_row(str(f.get("id", "?")), f.get("title", "?"), str(f.get("points", "?")), owned)
        from ..formatters import console
        console.print(table)
    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("own")
def own(
    fortress_id: int = typer.Argument(..., help="Fortress ID"),
    flag: str = typer.Argument(..., help="Flag to submit"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Submit a flag for a fortress."""
    try:
        data = api_post(f"/fortress/{fortress_id}/flag", {"flag": flag})
        if raw:
            print_json(data)
        else:
            if data.get("success"):
                print_success(data.get("message", "Flag accepted!"))
            else:
                print_error(data.get("message", "Flag rejected"))
    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("reset")
def reset(
    fortress_id: int = typer.Argument(..., help="Fortress ID"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Vote to reset a fortress."""
    try:
        data = api_post(f"/fortress/{fortress_id}/reset", {})
        if raw:
            print_json(data)
        else:
            from ..formatters import console
            msg = data.get("message", "Reset vote recorded")
            console.print(f"[green]{msg}[/green]")
    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)
