"""
Diagnostic test command.

Scans all HTB API endpoints used by htb-cli and reports which work
and which are broken. Helpful for detecting HTB API changes.
"""

from ..client import HTBClient, HTBError
from ..formatters import console, print_error, print_json, sanitize_text

import typer

app = typer.Typer(help="Run API endpoint diagnostics (helpful for debugging)", hidden=True)

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
        elif status in (400, 422, 500):
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
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
    raw: bool = typer.Option(False, "--raw", "-r", help="Output raw JSON"),
):
    """Run full API endpoint scan using live IDs.

    ⚠️  This makes real API calls including spawn/terminate/reset.
    """
    global RESULTS
    RESULTS = []

    if not yes:
        from ..formatters import print_warning
        print_warning("This will make real API calls (spawn, terminate, etc.)")
        try:
            typer.confirm("Continue?", abort=True)
        except typer.Abort:
            console.print("[dim]Aborted.[/dim]")
            raise typer.Exit(0)

    # Bootstrap: fetch valid IDs from working list endpoints
    client = HTBClient()
    try:
        machines = client.get("/machine/paginated", {"per_page": 1, "page": 1}).get("data", [])
        mid = machines[0]["id"] if machines else None

        chals = client.get("/challenge/list").get("challenges", [])
        cid = chals[0]["id"] if chals else None

        sherlocks = client.get("/sherlocks", {"per_page": 1, "page": 1}).get("data", [])
        sid = sherlocks[0]["id"] if sherlocks else None

        seasons = client.get("/season/list").get("data", [])
        season_id = seasons[0]["id"] if seasons else None
    except HTBError:
        mid = cid = sid = season_id = None
    finally:
        client.close()

    # Auth / User
    _test("GET", "/user/info", "user_info")
    _test("GET", "/search/fetch", "search_fetch", params={"query": "test"})

    # Connection / VPN
    _test("GET", "/connection/status", "conn_status")
    _test("GET", "/connections/servers", "conn_servers", params={"product": "labs"})
    _test("GET", "/v5/connections", "conn_v5")
    _test("GET", "/access/ovpnfile/0/0", "vpn_dl_tcp")
    _test("GET", "/access/ovpnfile/0/0/1", "vpn_dl_udp")

    # Machines
    _test("GET", "/machine/paginated", "machine_list", params={"per_page": 3, "page": 1})
    _test("GET", "/machine/list/retired/paginated", "machine_retired", params={"per_page": 3, "page": 1})
    _test("GET", "/machine/active", "machine_active")
    if mid:
        _test("GET", f"/machine/profile/{mid}", "machine_profile")
        _test("GET", f"/machine/writeup/{mid}", "machine_writeup")
        _test("GET", "/v5/machines", "v5_machines", params={"per_page": 3, "page": 1})
        _test("POST", "/vm/spawn", "vm_spawn", post_data={"machine_id": mid})
        _test("POST", "/vm/terminate", "vm_terminate", post_data={"machine_id": mid})
        _test("POST", "/vm/reset", "vm_reset", post_data={"machine_id": mid})
        _test("POST", "/v5/machine/own", "machine_own", post_data={"id": mid, "flag": "INVALID_FLAG_123", "difficulty": 0})
        _test("POST", f"/machine/todo/update/{mid}", "machine_todo", post_data={})
    else:
        RESULTS.append({"tag": "machine_profile", "method": "GET", "path": "/machine/profile/-", "result": "SKIP", "status": None, "note": "no valid machine ID"})

    # Challenges
    _test("GET", "/challenge/list", "challenge_list")
    _test("GET", "/challenge/list/retired", "challenge_retired")
    _test("GET", "/challenge/categories/list", "challenge_cats")
    if cid:
        _test("GET", f"/challenge/info/{cid}", "challenge_info")
        _test("GET", f"/challenge/download/{cid}", "challenge_dl")
        _test("POST", "/container/start", "container_start", post_data={"challenge_id": cid})
        _test("POST", "/container/stop", "container_stop", post_data={"challenge_id": cid})
        _test("POST", "/challenge/own", "challenge_own", post_data={"challenge_id": cid, "flag": "INVALID"})
    else:
        RESULTS.append({"tag": "challenge_info", "method": "GET", "path": "/challenge/info/-", "result": "SKIP", "status": None, "note": "no valid challenge ID"})

    # Sherlocks
    _test("GET", "/sherlocks", "sherlock_list", params={"per_page": 3, "page": 1})
    if sid:
        _test("GET", f"/sherlocks/{sid}", "sherlock_info")
        _test("GET", f"/sherlocks/{sid}/tasks", "sherlock_tasks")
        _test("GET", f"/sherlocks/{sid}/download_link", "sherlock_dl")
        _test("POST", f"/sherlocks/{sid}/tasks/1/flag", "sherlock_own", post_data={"flag": "INVALID"})
    else:
        RESULTS.append({"tag": "sherlock_info", "method": "GET", "path": "/sherlocks/-", "result": "SKIP", "status": None, "note": "no valid sherlock ID"})

    # Seasons
    _test("GET", "/season/list", "season_list")
    _test("GET", "/season/machines", "season_machines")
    _test("GET", "/season/machine/active", "season_machine_active")
    if season_id:
        _test("GET", f"/season/user/rank/{season_id}", "season_rank")
        _test("GET", f"/season/players/leaderboard/top/{season_id}", "season_lb")
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
