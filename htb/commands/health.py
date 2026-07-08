"""
HTB infrastructure health check.

Displays real-time status of HTB services by scraping
https://status.hackthebox.com/ (no auth required).
"""

from ..client import fetch_infra_status
from ..formatters import console, print_error, print_json

import httpx
import typer

app = typer.Typer(help="Check HTB service health (status.hackthebox.com)")


@app.callback(invoke_without_command=True)
def health(
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Show real-time status of HTB platforms and backend services."""
    try:
        results = fetch_infra_status()

        if raw:
            print_json(results)
            return

        if not results:
            console.print("[yellow]No status data available.[/yellow]")
            return

        from ..formatters import print_infra_health

        print_infra_health(results)

    except httpx.HTTPError as e:
        print_error(f"Failed to fetch status page: {e}")
        raise typer.Exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        raise typer.Exit(1)
