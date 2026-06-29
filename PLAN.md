# htb-cli Rewrite Plan

## Priority: v5 first, v4 only if v5 doesn't exist for an endpoint

---

## Phase 1: Fix Intuitiveness & Renames

### 1.1 Fix `machine unreleased`
- **Problem:** Calls `GET /v5/machines` with no state filter — shows ALL machines, not unreleased.
- **Fix:** Either pass `?state=unreleased` to v5 endpoint, or remove the standalone subcommand.
- ✨ **Decision:** Merge into `machine list --state unreleased` (see 2.1).

### 1.2 Merge `machine todo` into list
- `machine todo` → `machine list --todo` flag instead of standalone command.
- `machine add-todo` stays (it toggles, can't be a flag).
- ✨ **Decision:** Add `--todo`/`--incomplete`/`--completed` flags to `machine list`. Remove `machine todo` subcommand.

### 1.3 Clean up season naming
| Current | Issue | Fix |
|---|---|---|
| `season machines` | Shows current season machines | Rename to `machine list --season` or keep as `season machines` but add `--season-id` to pick specific season |
| `season active` | Shows active season machines | Rename to `season active-machines` for clarity |
| `season own` | Posts to `/arena/own`, not season | Rename to `season arena-own` or add `arena` as a command group |
- ✨ **Decision:** `season machines` → add `--season-id` param. `season active` → `season active-machines`. `season own` → `season arena-own`.

### 1.4 Inconsistent challenge/machine semantics
| Current | Issue |
|---|---|
| `challenge start <name>` | Requires name (good) |
| `challenge stop <name>` | Requires name (but only 1 docker runs at a time, shouldn't need it) |
| `challenge active` | Shows running docker (fine) |
| `machine stop` | Auto-detects active machine (good) |
| `machine reset` | Auto-detects active machine (good) |
| `machine spawn <name>` | Requires name (good) |
- ✨ **Decision:** Make `challenge stop` auto-detect active docker (consistent with `machine stop`). Make `challenge own` still accept `--challenge` flag to override.

### 1.5 Add `--raw` to `add-todo`
- Minor consistency fix — just add the flag.

### 1.6 `sherlock own` args
- Sherlock own takes `NAME FLAG` as positionals, challenge own takes `FLAG` with `--challenge` option.
- ✨ **Decision:** Keep sherlock own as-is (you already have the name in context when working on a sherlock). Or change to `FLAG` with `--sherlock` option for consistency. Keep for now.

---

## Phase 2: v5 Machine Endpoints (Full Coverage)

### 2.1 `machine list` — Rewrite using `GET /v5/machines`

**Current (v4):** `/machine/paginated` and `/machine/list/retired/paginated`
**Target (v5):** `GET /v5/machines`

**v5 supported params & flags:**

| Flag | Type | v5 param | Description |
|---|---|---|---|
| `--page` / `-p` | int | `page` | Page number |
| `--per-page` / `-n` | int | `per_page` | Items per page |
| `--state` | enum | `state` | `active`, `retired`, `unreleased`, `todo`? |
| `--difficulty` / `-d` | enum | `difficulty` | `easy`, `medium`, `hard`, `insane` |
| `--os` | enum | `os` | `windows`, `linux`, `freebsd`, `solaris` |
| `--search` / `-q` | string | `keyword` | Search by name |
| `--free` | bool | `free` | Free machines only |
| `--todo` | bool | `todo` | Only todo-listed machines |
| `--completed` | bool | `show_completed` | Show completed |
| `--incomplete` | bool | (client-side filter) | Show incompleted |
| `--sort-by` / `-s` | enum | `sort_by` | `name`, `difficulty`, `release`, `rating`, `points` |
| `--sort-type` | enum | `sort_type` | `asc`, `desc` |
| `--sp-tier` | int | `sp_tier` | Starting Point tier ID |
| `--raw` / `-r` | bool | — | JSON output |

### 2.2 `machine info` — Check v5
- v4: `GET /machine/profile/{slug}`.
- v5: Not available — keep v4.

### 2.3 `machine active` — Check v5
- v4: `GET /machine/active`.
- v5: `GET /v5/virtual_machine/active` (different response shape — has `info` wrapper with VM details).
- ✨ **Decision:** Use v5 endpoint, but keep `machine active` command name.

### 2.4 `machine own` — Already on v5
- Currently uses `POST /v5/machine/own`. ✓ Good.

### 2.5 Machine graph/matrix data
- v4: `GET /machine/graph/matrix/{id}`
- Not a priority command, could be `machine ratings <name>` later.

### 2.6 Machine walkthroughs
- v4 available. Low priority.

---

## Phase 3: v5 Challenge Endpoints

### 3.1 `challenge list` — Migrate to paginated endpoint
- Current: `GET /challenge/list` (non-paginated).
- v4 paginated alternative: `GET /challenges` (note the `s` — different endpoint).
- Supports: `page`, `per_page`, `difficulty`, `keyword`, `category`, `status`, `state`, `sort_by`, `sort_type`, `todo`.
- ✨ **Decision:** Add pagination, search, sort, and `--todo` flag.

### 3.2 Challenge writeups
- `GET /challenge/{id}/writeup` and `/challenge/{id}/writeup/official`.
- ✨ **Decision:** Add `challenge writeup <name>` command (mirrors `machine writeup`).

### 3.3 Challenge activity
- `GET /challenge/activity/{id}` — users who solved it.
- ✨ **Decision:** Add `challenge activity <name>` command.

---

## Phase 4: v5 Connection/VPN Endpoints

### 4.1 `vpn connections` — Already on v5
- Currently uses `GET /v5/connections`. ✓ Good.

### 4.2 Prolab VPN servers
- v4: `GET /connections/servers/prolab/{prolabId}`.
- ✨ **Decision:** Add `vpn servers --prolab-id` flag.

---

## Phase 5: New Domains (v5 first)

### 5.1 Pwnbox (`htb pwnbox`)
| Command | API | Description |
|---|---|---|
| `pwnbox status` | `GET /v4/pwnbox/status` | Current Pwnbox status |
| `pwnbox start` | `POST /v4/pwnbox/start` | Start Pwnbox |
| `pwnbox stop` | `POST /v4/pwnbox/terminate` | Stop Pwnbox |
| `pwnbox usage` | `GET /v4/pwnbox/usage` | Usage stats |

### 5.2 User Dashboard (v5)
| Command | API | Description |
|---|---|---|
| `dashboard favorites` | `GET /v5/user/dashboard/favorites` | User's favorite/owned machines |
| `dashboard inprogress` | `GET /v5/user/dashboard/inprogress` | In-progress items |
| `dashboard recommended` | `GET /v5/user/dashboard/recommended` | Recommended items |

### 5.3 Profile (v5)
| Command | API | Description |
|---|---|---|
| `profile basic <user-id>` | `GET /v4/user/profile/basic/{userId}` | View other user's profile |
| `profile badges <user-id>` | `GET /v4/user/profile/badges/{userId}` | User's badges |
| `profile activity <user-id>` | `GET /v5/user/profile/activity/{userId}` | User's recent activity |
| `profile content <user-id>` | `GET /v5/user/profile/content/{userId}` | User's solves/owns |

---

## Phase 6: v4-only Endpoints (No v5 equivalent)

### 6.1 Fortresses
| Command | API |
|---|---|
| `fortress list` | `GET /v4/fortresses` |
| `fortress info <id>` | `GET /v4/fortress/{id}` |
| `fortress flags <id>` | `GET /v4/fortress/{id}/flags` |
| `fortress own <id> <flag>` | `POST /v4/fortress/{id}/flag` |
| `fortress reset <id>` | `POST /v4/fortress/{id}/reset` |

### 6.2 Tracks
| Command | API |
|---|---|
| `track list` | `GET /v4/tracks` |
| `track info <id>` | `GET /v4/tracks/{id}` |
| `track enroll <id>` | `POST /v4/tracks/enroll/{id}` |
| `track like <id>` | `POST /v4/tracks/like/{id}` |

### 6.3 Rankings
| Command | API |
|---|---|
| `ranking users` | `GET /v4/rankings/users` |
| `ranking countries` | `GET /v4/rankings/countries` |
| `ranking teams` | `GET /v4/rankings/teams` |
| `ranking universities` | `GET /v4/rankings/universities` |
| `ranking country-members <code>` | `GET /v4/rankings/country/{code}/members` |

### 6.4 Teams
| Command | API |
|---|---|
| `team info <id>` | `GET /v4/team/info/{id}` |
| `team members <id>` | `GET /v4/team/members/{id}` |
| `team activity <id>` | `GET /v4/team/activity/{id}` |

### 6.5 Sherlocks enhancements
| Command | API |
|---|---|
| `sherlock categories` | `GET /v4/sherlocks/categories/list` |
| `sherlock progress <name>` | `GET /v4/sherlocks/{id}/progress` |
| `sherlock writeup <name>` | `GET /v4/sherlocks/{id}/writeup` |

---

## Phase 7: Output Enhancements

### 7.1 Color active machines in machine lists
- In `machine list`, `season machines`, etc., if a machine in the list is the currently spawned active one, highlight its row in **green** or a distinctive color.
- Can check against the active machine ID from `/machine/active` (or `/v5/virtual_machine/active`).

### 7.2 Consistent table formatting
- All list commands should show pagination info (page X/Y, total).
- All list commands should support `--raw`.
- Use consistent column ordering across similar commands.

### 7.3 Richer `machine info` output
Show additional fields from v4 profile endpoint:
- User/root owns count
- Release/retire dates
- Rating distribution (graph matrix)
- Tags (attack path, language)
- Creator info

### 7.4 Richer `challenge info` output
- Show container info if running (IP:port)
- Show solve count, rating

---

## Phase 8: Technical Debt

### 8.1 v5 client methods
- Add `get_v5()` convenience method to client, for endpoints under v5 base.
- Currently mixed: `/v5/machine/own` uses `api_post("/v5/machine/own")`, `/v5/connections` uses `api_get("/v5/connections")`.
- Clean up path construction.

### 8.2 Error handling consistency
- Normalize error messages across all commands.
- Ensure auth errors are caught properly everywhere.

### 8.3 Global `--raw` flag
- Consider making `--raw` a global flag at the root level instead of per-command.

### 8.4 Machine name resolution
- `_find_machine_by_name()` falls back from profile to paginated search. When we migrate to v5, the paginated fallback should use `GET /v5/machines`.

---

## Implementation Order

1. **Phase 1** — Fix intuitiveness (easy wins, no new endpoints)
2. **Phase 2** — v5 machine rewrite (core functionality)
3. **Phase 7.1** — Color active machines (UX improvement)
4. **Phase 5.1** — Pwnbox commands (simple, popular)
5. **Phase 3** — Challenge enhancements
6. **Phase 5.2-5.3** — Dashboard & Profile (v5)
7. **Phase 6.1-6.5** — v4-only domains
8. **Phase 8** — Technical debt cleanup
