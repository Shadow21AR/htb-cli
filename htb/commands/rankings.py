"""Ranking commands.

Commands:
- htb ranking users             - Top users
- htb ranking countries         - Top countries
- htb ranking teams             - Top teams
- htb ranking universities      - Top universities
- htb ranking country-members   - Members of a country
"""

import typer

from ..client import HTBError, api_get
from ..formatters import (
    print_countries,
    print_country_members,
    print_error,
    print_json,
    print_ranking_entries,
    print_universities,
)

app = typer.Typer(help="Ranking/leaderboard management")


@app.command("users")
def users(
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Top-ranked users."""
    try:
        data = api_get("/rankings/users")
        if raw:
            print_json(data)
            return
        entries = data.get("data", [])
        print_ranking_entries(entries, "User Rankings")
    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("teams")
def teams(
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Top-ranked teams."""
    try:
        data = api_get("/rankings/teams")
        if raw:
            print_json(data)
            return
        entries = data.get("data", [])
        print_ranking_entries(entries, "Team Rankings")
    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("countries")
def countries(
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Top-ranked countries."""
    try:
        data = api_get("/rankings/countries")
        if raw:
            print_json(data)
            return
        entries = data.get("data", [])
        print_countries(entries)
    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("universities")
def universities(
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Top-ranked universities."""
    try:
        data = api_get("/rankings/universities")
        if raw:
            print_json(data)
            return
        entries = data.get("data", [])
        print_universities(entries)
    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("country-members")
def country_members(
    country_code: str = typer.Argument(..., help="Two-letter country code (e.g. US, DE)"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Members of a country ranking."""
    try:
        data = api_get(f"/rankings/country/{country_code.upper()}/members")
        if raw:
            print_json(data)
            return
        entries = data.get("data", {}).get("rankings", [])
        print_country_members(entries, country_code.upper())
    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)
