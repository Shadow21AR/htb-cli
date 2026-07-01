"""
VPN and connection management commands.

Commands:
- htb vpn status      - Show connection status
- htb vpn servers     - List available VPN servers
- htb vpn switch      - Switch to a different server
- htb vpn download    - Download VPN config file
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import typer

from ..client import HTBError, api_download, api_get, api_get_v5, api_post
from ..files import resolve_output_path
from ..formatters import (
    console,
    print_connection_status,
    print_error,
    print_json,
    print_key_value,
    print_servers,
    print_success,
)

app = typer.Typer(help="VPN and connection management")


class Product(str, Enum):
    """HTB product types for VPN."""
    labs = "labs"
    competitive = "competitive"
    fortresses = "fortresses"
    starting_point = "starting_point"


@app.command("status")
def status(
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Show current VPN connection status."""
    try:
        data = api_get("/connection/status")

        if raw:
            print_json(data)
        else:
            print_connection_status(data)

    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)


def _parse_server_options(data: dict) -> list[dict]:
    """Parse nested server structure from /connections/servers response.

    Response shape: {data: {disabled, assigned, options: {Region: {LocationType: {location, name, servers: {id: server}}}}}}
    """
    all_servers: list[dict[str, Any]] = []
    options = data.get("data", {}).get("options", {})
    for region_name, region_data in options.items():
        if isinstance(region_data, dict):
            for location_name, location_data in region_data.items():
                if isinstance(location_data, dict) and "servers" in location_data:
                    servers_dict = location_data["servers"]
                    if isinstance(servers_dict, dict):
                        server_list = servers_dict.values()
                    else:
                        server_list = servers_dict
                    for srv in server_list:
                        srv["location"] = location_data.get("name", location_name)
                        all_servers.append(srv)
    return all_servers


@app.command("servers")
def servers(
    product: Product = typer.Option(Product.labs, "--product", "-p", help="Product type (labs, competitive, fortresses, starting_point)"),
    prolab_id: Optional[int] = typer.Option(None, "--prolab-id", help="Pro Lab ID to get VPN servers for"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """List available VPN servers."""
    try:
        if prolab_id is not None:
            data = api_get(f"/connections/servers/prolab/{prolab_id}")
        else:
            data = api_get("/connections/servers", {"product": product.value})

        if raw:
            print_json(data)
            return

        all_servers = _parse_server_options(data)
        title = f"Pro Lab {prolab_id} VPN Servers" if prolab_id is not None else "VPN Servers"
        print_servers(all_servers, title)

    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("connections")
def connections(
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Show all active connections across products."""
    try:
        data = api_get_v5("/connections")

        if raw:
            print_json(data)
            return

        # Display each product's connection (v5 returns a list under "data")
        for item in data.get("data", []):
            srv = item.get("assigned_server")
            if srv:
                info = {
                    "Product": item.get("type", "").replace("_", " ").title(),
                    "Server": srv.get("friendly_name"),
                    "Server ID": srv.get("id"),
                    "Users": srv.get("current_clients"),
                    "Location": item.get("location_type_friendly"),
                }
                pro_lab = item.get("pro_lab")
                if pro_lab:
                    info["Pro Lab"] = pro_lab.get("name")

                print_key_value(info, item.get("type", "UNKNOWN").upper())
                console.print()

    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("switch")
def switch(
    server_id: int = typer.Argument(..., help="Server ID to switch to"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Switch to a different VPN server."""
    try:
        data = api_post(f"/connections/servers/switch/{server_id}")

        if raw:
            print_json(data)
        else:
            server_info = data.get("data", {})
            print_success(f"Switched to: {server_info.get('friendly_name', server_id)}")

    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)


@app.command("download")
def download(
    server_id: int = typer.Argument(..., help="Server ID to download VPN for"),
    udp: bool = typer.Option(False, "--udp", "-u", help="Download UDP config (default: TCP)"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path"),
):
    """Download VPN configuration file."""
    try:
        # Build endpoint path (TCP by default)
        if udp:
            path = f"/access/ovpnfile/{server_id}/0"
        else:
            path = f"/access/ovpnfile/{server_id}/0/1"

        content = api_download(path)

        # Generate filename if not specified
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        protocol = "udp" if udp else "tcp"
        filename = f"htb-{server_id}-{protocol}-{timestamp}.ovpn"
        path = resolve_output_path(output, filename)
        path.write_text(content)
        print_success(f"VPN config saved to: {path}")

    except HTBError as e:
        print_error(e.message)
        raise typer.Exit(1)
