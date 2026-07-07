"""
Live endpoint scanner for HTB API.

Tests every endpoint used by htb-cli against the real HTB API.
Reports which endpoints work, which are broken, and response shapes.

Usage:
    python tests/test_endpoints_live.py
"""

import os
import sys
import json
import time
from typing import Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from htb.client import HTBClient, HTBError
from htb.config import Config

RESULTS: list[dict[str, Any]] = []

PASS = "PASS"
BROKEN = "BROKEN"
AUTH_FAIL = "AUTH_FAIL"
SKIP = "SKIP"


def test_endpoint(
    method: str,
    path: str,
    tag: str,
    params: dict | None = None,
    post_data: dict | None = None,
    use_download: bool = False,
    use_download_bytes: bool = False,
    skip_reason: str | None = None,
):
    if skip_reason:
        RESULTS.append({"tag": tag, "method": method, "path": path, "result": SKIP, "status": None, "note": skip_reason})
        return

    client = HTBClient()
    try:
        start = time.time()
        if use_download:
            resp = client.download(path)
        elif use_download_bytes:
            resp = client.download_bytes(path)
        elif method == "GET":
            resp = client.get(path, params)
        elif method == "POST":
            resp = client.post(path, post_data)
        else:
            raise ValueError(f"Unknown method: {method}")
        elapsed = round(time.time() - start, 2)

        RESULTS.append({"tag": tag, "method": method, "path": path, "result": PASS, "status": 200, "note": f"OK ({elapsed}s)"})

    except HTBError as e:
        elapsed = round(time.time() - start, 2)
        status = e.status_code
        msg = str(e.message)[:120]

        if status in (401, 403):
            result = AUTH_FAIL
        elif status == 400 or status == 422:
            # endpoint exists, our dummy data was rejected — good sign
            result = PASS
        else:
            result = BROKEN

        RESULTS.append({"tag": tag, "method": method, "path": path, "result": result, "status": status, "note": f"{msg} ({elapsed}s)"})

    except Exception as e:
        RESULTS.append({"tag": tag, "method": method, "path": path, "result": BROKEN, "status": None, "note": str(e)[:120]})
    finally:
        client.close()


def _print_report():
    print("\n" + "=" * 110)
    print("  HTB API ENDPOINT SCAN RESULTS")
    print("=" * 110)

    pass_count = sum(1 for r in RESULTS if r["result"] == PASS)
    broken_count = sum(1 for r in RESULTS if r["result"] == BROKEN)
    auth_count = sum(1 for r in RESULTS if r["result"] == AUTH_FAIL)
    skip_count = sum(1 for r in RESULTS if r["result"] == SKIP)

    print(f"\n  PASS={pass_count}  BROKEN={broken_count}  AUTH_FAIL={auth_count}  SKIP={skip_count}")
    print()

    broken = [r for r in RESULTS if r["result"] in (BROKEN, AUTH_FAIL)]
    if broken:
        print("  ┌─── BROKEN / AUTH_FAIL ──────────────────────────────────────────────────")
        for r in broken:
            s = f"HTTP {r['status']}" if r["status"] else "NO_CONN"
            print(f"  │ {r['method']:6s} {s:10s}  {r['tag']:25s} {r['path']}")
            print(f"  │ {'':6s} {'':10s}  {'':25s} {r['note']}")
        print("  └──────────────────────────────────────────────────────────────────────────")
        print()

    print(f"  {'METHOD':6s} {'STATUS':10s} {'RESULT':8s} {'TAG':25s} {'PATH'}")
    print(f"  {'-'*6} {'-'*10} {'-'*8} {'-'*25} {'-'*50}")
    for r in RESULTS:
        s = f"HTTP {r['status']}" if r["status"] else "N/A"
        print(f"  {r['method']:6s} {s:10s} {r['result']:8s} {r['tag']:25s} {r['path']}")

    if broken_count > 0:
        print(f"\n  ⚠  {broken_count} endpoint(s) are BROKEN.")
    else:
        print(f"\n  ✓ All {pass_count} endpoints OK.")


def test_all_endpoints():
    token = os.environ.get("HTB_TOKEN")
    if not token:
        print("ERROR: HTB_TOKEN not set. Export your token and try again.")
        sys.exit(1)

    token = token.strip()
    os.environ["HTB_TOKEN"] = token

    # ── Auth / User ──────────────────────────────────
    test_endpoint("GET", "/user/info", "user_info")
    test_endpoint("GET", "/search/fetch", "search_fetch", params={"query": "test"})

    # ── Connection / VPN ─────────────────────────────
    test_endpoint("GET", "/connection/status", "conn_status")
    test_endpoint("GET", "/connection/status/lab", "conn_status_lab")
    test_endpoint("GET", "/connection/status/competitive", "conn_status_comp")
    test_endpoint("GET", "/connection/status/starting_point", "conn_status_sp")
    test_endpoint("GET", "/connections", "connections_all")
    test_endpoint("GET", "/connections/servers", "conn_servers", params={"product": "labs"})
    test_endpoint("POST", "/connections/servers/switch/0", "conn_switch", post_data={})
    test_endpoint("GET", "/access/ovpnfile/0/0", "vpn_dl_tcp", use_download=True)
    test_endpoint("GET", "/access/ovpnfile/0/0/1", "vpn_dl_udp", use_download=True)

    # ── Machines ─────────────────────────────────────
    test_endpoint("GET", "/machine/paginated", "machine_list", params={"per_page": 3, "page": 1})
    test_endpoint("GET", "/machine/list/retired/paginated", "machine_retired", params={"per_page": 3, "page": 1})
    test_endpoint("GET", "/machine/active", "machine_active")
    test_endpoint("GET", "/machine/unreleased", "machine_unreleased", params={"per_page": 3, "page": 1})
    test_endpoint("GET", "/machine/profile/1", "machine_profile")
    test_endpoint("GET", "/machine/writeup/1", "machine_writeup")

    # POST: check endpoint exists (dummy data)
    test_endpoint("POST", "/vm/spawn", "vm_spawn", post_data={"machine_id": 999999})
    test_endpoint("POST", "/vm/terminate", "vm_terminate", post_data={"machine_id": 999999})
    test_endpoint("POST", "/vm/reset", "vm_reset", post_data={"machine_id": 999999})
    test_endpoint("POST", "/v5/machine/own", "machine_own", post_data={"id": 999999, "flag": "INVALID_FLAG_123", "difficulty": 0})
    test_endpoint("POST", "/machine/todo/update/999999", "machine_todo", post_data={})

    # ── Challenges ────────────────────────────────────
    test_endpoint("GET", "/challenge/list", "challenge_list")
    test_endpoint("GET", "/challenge/list/retired", "challenge_retired")
    test_endpoint("GET", "/challenge/categories/list", "challenge_cats")
    test_endpoint("GET", "/challenge/info/1", "challenge_info")
    test_endpoint("GET", "/challenge/download/999999", "challenge_dl", use_download_bytes=True)

    test_endpoint("POST", "/challenge/start", "challenge_start", post_data={"challenge_id": 999999})
    test_endpoint("POST", "/challenge/stop", "challenge_stop", post_data={"challenge_id": 999999})
    test_endpoint("POST", "/challenge/own", "challenge_own", post_data={"challenge_id": 999999, "flag": "INVALID"})

    # ── Sherlocks ────────────────────────────────────
    test_endpoint("GET", "/sherlocks", "sherlock_list", params={"per_page": 3, "page": 1})
    test_endpoint("GET", "/sherlocks/1", "sherlock_info")
    test_endpoint("GET", "/sherlocks/1/tasks", "sherlock_tasks")
    test_endpoint("GET", "/sherlocks/1/download_link", "sherlock_dl", use_download_bytes=True)

    test_endpoint("POST", "/sherlocks/1/tasks/1/flag", "sherlock_own", post_data={"flag": "INVALID"})

    # ── Seasons ───────────────────────────────────────
    test_endpoint("GET", "/season/list", "season_list")
    test_endpoint("GET", "/season/machines", "season_machines")
    test_endpoint("GET", "/season/machine/active", "season_machine_active")
    test_endpoint("GET", "/season/user/rank/1", "season_rank")
    test_endpoint("GET", "/season/players/leaderboard/top/1", "season_lb")

    test_endpoint("POST", "/arena/own", "arena_own", post_data={"id": 999999, "flag": "INVALID"})

    _print_report()


if __name__ == "__main__":
    test_all_endpoints()
