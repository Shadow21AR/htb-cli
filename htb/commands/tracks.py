"""Track commands.

Commands:
- htb track list       - List tracks
- htb track info       - Get track details
- htb track enroll     - Enroll in a track
- htb track like       - Like a track
"""

import typer

from ..client import HTBError, api_get, api_post
from ..formatters import print_error, print_json, print_success, print_track, print_tracks

app = typer.Typer(help="Track management")


@app.command("list")
def list_tracks(
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """List all available tracks."""
    try:
        data = api_get("/tracks")
        if raw:
            print_json(data)
            return

        tracks = data if isinstance(data, list) else data.get("data", [])
        print_tracks(tracks)
    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("info")
def info(
    track_id: int = typer.Argument(..., help="Track ID"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Get detailed information about a track."""
    try:
        data = api_get(f"/tracks/{track_id}")
        if raw:
            print_json(data)
            return

        print_track(data)
    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("enroll")
def enroll(
    track_id: int = typer.Argument(..., help="Track ID"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Enroll in a track."""
    try:
        data = api_post(f"/tracks/enroll/{track_id}", {})
        if raw:
            print_json(data)
        else:
            msg = data.get("message", "Enrolled successfully")
            print_success(msg)
    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("like")
def like(
    track_id: int = typer.Argument(..., help="Track ID"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Like a track."""
    try:
        data = api_post(f"/tracks/like/{track_id}", {})
        if raw:
            print_json(data)
        else:
            msg = data.get("message", "Track liked!")
            print_success(msg)
    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)
