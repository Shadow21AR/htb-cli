"""
Diagnostic test command.

Scans all HTB API endpoints used by htb-cli and reports which work
and which are broken. Helpful for detecting HTB API changes.
"""

from ..client import HTBClient, HTBError
from ..formatters import console, print_error, print_json, sanitize_text

import typer

app = typer.Typer(help="Run API endpoint diagnostics (helpful for debugging)")

PASS = "PASS"
BROKEN = "BROKEN"
AUTH_FAIL = "AUTH_FAIL"

RESULTS: list[dict] = []


def _test(method: str, path: str, tag: str, params: dict | None = None, post_data: dict | None = None):
    client = HTBClient()
    try:
        if method == "GET":
            client.get(path, params)
        elif method == "POST":
            client.post(path, post_data or {})
        RESULTS.append({"tag": tag, "method": method, "path": path, "result": PASS, "status": 200, "note": "OK"})

    except HTBError as e:
        status = e.status_code
        msg = str(e.message)[:120]
        if status in (401, 403):
            result = AUTH_FAIL
        elif status == 400 or status == 422:
            result = PASS
        else:
            result = BROKEN
        RESULTS.append({"tag": tag, "method": method, "path": path, "result": result, "status": status, "note": msg})
    except Exception as e:
        RESULTS.append({"tag": tag, "method": method, "path": path, "result": BROKEN, "status": None, "note": str(e)[:120]})
    finally:
        client.close()


@app.command("all")
def test_all(
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Run full API endpoint scan."""
    global RESULTS
    RESULTS = []

    # Auth / User
    _test("GET", "/user/info", "user_info")
    _test("GET", "/search/fetch", "search_fetch", params={"query": "test"})

    # Connection / VPN
    _test("GET", "/connection/status", "conn_status")
    _test("GET", "/connections/servers", "conn_servers", params={"product": "labs"})
    _test("GET", "/v5/connections", "conn_v5")
    _test("POST", "/connections/servers/switch/0", "conn_switch", post_data={})
    _test("GET", "/access/ovpnfile/0/0", "vpn_dl_tcp")
    _test("GET", "/access/ovpnfile/0/0/1", "vpn_dl_udp")

    # Machines
    _test("GET", "/machine/paginated", "machine_list", params={"per_page": 3, "page": 1})
    _test("GET", "/machine/list/retired/paginated", "machine_retired", params={"per_page": 3, "page": 1})
    _test("GET", "/machine/active", "machine_active")
    _test("GET", "/machine/profile/1", "machine_profile")
    _test("GET", "/machine/writeup/1", "machine_writeup")
    _test("GET", "/v5/machines", "v5_machines", params={"per_page": 3, "page": 1})
    _test("POST", "/vm/spawn", "vm_spawn", post_data={"machine_id": 999999})
    _test("POST", "/vm/terminate", "vm_terminate", post_data={"machine_id": 999999})
    _test("POST", "/vm/reset", "vm_reset", post_data={"machine_id": 999999})
    _test("POST", "/v5/machine/own", "machine_own", post_data={"id": 999999, "flag": "INVALID_FLAG_123", "difficulty": 0})
    _test("POST", "/machine/todo/update/999999", "machine_todo", post_data={})

    # Challenges
    _test("GET", "/challenge/list", "challenge_list")
    _test("GET", "/challenge/list/retired", "challenge_retired")
    _test("GET", "/challenge/categories/list", "challenge_cats")
    _test("GET", "/challenge/info/1", "challenge_info")
    _test("GET", "/challenge/download/999999", "challenge_dl")
    _test("POST", "/container/start", "container_start", post_data={"challenge_id": 999999})
    _test("POST", "/container/stop", "container_stop", post_data={"challenge_id": 999999})
    _test("POST", "/challenge/own", "challenge_own", post_data={"id": 999999, "flag": "INVALID", "difficulty": 0})

    # Sherlocks
    _test("GET", "/sherlocks", "sherlock_list", params={"per_page": 3, "page": 1})
    _test("GET", "/sherlocks/1", "sherlock_info")
    _test("GET", "/sherlocks/1/tasks", "sherlock_tasks")
    _test("GET", "/sherlocks/1/download_link", "sherlock_dl")
    _test("POST", "/sherlocks/1/tasks/1/flag", "sherlock_own", post_data={"flag": "INVALID"})

    # Seasons
    _test("GET", "/season/list", "season_list")
    _test("GET", "/season/machines", "season_machines")
    _test("GET", "/season/machine/active", "season_machine_active")
    _test("GET", "/season/user/rank/1", "season_rank")
    _test("GET", "/season/players/leaderboard/top/1", "season_lb")
    _test("POST", "/arena/own", "arena_own", post_data={"id": 999999, "flag": "INVALID"})

    if raw:
        print_json(RESULTS)
        return

    pass_count = sum(1 for r in RESULTS if r["result"] == PASS)
    broken_count = sum(1 for r in RESULTS if r["result"] == BROKEN)
    auth_count = sum(1 for r in RESULTS if r["result"] == AUTH_FAIL)

    console.print(f"\n[bold]HTB API Endpoint Scan[/bold]")
    console.print(f"  Pass: [green]{pass_count}[/green]  Broken: [red]{broken_count}[/red]  Auth issues: [yellow]{auth_count}[/yellow]\n")

    broken = [r for r in RESULTS if r["result"] in (BROKEN, AUTH_FAIL)]
    if broken:
        console.print("[red]Broken endpoints:[/red]")
        for r in broken:
            s = f"HTTP {r['status']}" if r["status"] else "NO_CONN"
            console.print(f"  {r['method']:6s} {s:10s}  {r['tag']:25s} {sanitize_text(r['note'])[:100]}")

    console.print("\n[dim]Full results:[/dim]")
    for r in RESULTS:
        s = f"HTTP {r['status']}" if r["status"] else "N/A"
        c = "green" if r["result"] == PASS else ("red" if r["result"] == BROKEN else "yellow")
        console.print(f"  [{c}]{r['result']:8s}[/{c}] {r['method']:6s} {s:10s} {r['tag']:25s} {r['path']}")
