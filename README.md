# HTB CLI

Clean, modular command-line interface for the Hack The Box API.

![Demo](demo.gif)

## Features

- **Machines** — List, spawn, stop, reset, submit flags, todo list, writeups, achievements
- **Challenges** — Browse, start docker containers, download files, submit flags
- **Sherlocks** — DFIR investigations with multi-task support
- **VPN** — Manage connections, download configs, filter by product/prolab
- **Seasons/Arena** — Competitive season machine tracking and flag submission
- **Dashboard** — Favorites, in-progress, recommended items
- **Profile** — View user profiles, badges, activity, content stats
- **Pwnbox** — Start, stop, status, usage statistics
- **Fortresses** — List, info, flags, own, reset
- **Tracks** — List, info, enroll, like
- **Rankings** — Users, teams, countries, universities leaderboards
- **Teams** — Info, members, activity
- **Experience API** — Level, XP, streak shown in `whoami` and `status`

## Installation

```bash
pipx install htb-terminal
```

For OS keyring support:

```bash
pipx install "htb-terminal[auth]"
```

Falls back to `~/.config/htb-cli/token` (mode `0600`) if no keyring is available.

If already installed without extras:

```bash
pipx inject htb-terminal keyring
```

## Setup

Get your API token from [HTB App Settings](https://app.hackthebox.com/account-settings).

```bash
# Store securely (keyring preferred, file fallback)
htb auth set

# Or via env var (overrides stored token)
export HTB_TOKEN='your-token-here'
```

## Usage

### Overview

```bash
htb status              # User info, VPN connection, active machine
htb whoami              # Stylish profile with level, XP, streak
htb search linux        # Global search
```

### Auth

```bash
htb auth set            # Store token (prompts securely)
htb auth show           # Show token source (never leaks token)
htb auth status         # Validate token, show user info
htb auth unset          # Remove stored token
```

### Machines

```bash
htb machine list                        # Active machines (default)
htb machine list --state retired        # Retired machines
htb machine list --state unreleased     # Upcoming machines
htb machine list --difficulty easy      # Filter by difficulty
htb machine list --os linux             # Filter by OS (repeatable)
htb machine list --search "gavel"       # Search by name
htb machine list --sort name            # Sort: name|difficulty|release|rating|points
htb machine list --todo                 # Todo-listed only
htb machine list --free                 # Free machines only
htb machine list --completed            # Completed only
htb machine list --incomplete           # Incomplete only
htb machine info Gavel                  # Machine details
htb machine spawn Gavel                 # Spawn by name or ID
htb machine active                      # Current spawned machine
htb machine stop                        # Terminate active machine
htb machine reset                       # Reset active machine
htb machine own 'flag_value'            # Submit flag (use -d for difficulty)
htb machine add-todo Gavel              # Toggle todo on/off
htb machine writeup Gavel               # Official writeup URL (VIP)
htb machine achievement                 # Shareable URL for active machine
htb machine achievement Gavel           # Shareable URL for a specific machine
```

### Challenges

```bash
htb challenge list                      # Active challenges (default)
htb challenge list --state retired      # Retired challenges
htb challenge list --state unreleased   # Upcoming challenges
htb challenge list --category web       # Filter by category (repeatable)
htb challenge list --difficulty easy    # Filter by difficulty (repeatable)
htb challenge list --search "name"      # Search by name
htb challenge list --todo               # Todo-listed only
htb challenge list --completed          # Completed only
htb challenge list --incomplete         # Incomplete only
htb challenge categories                # List all categories
htb challenge info "Reminiscent"        # Challenge details
htb challenge start "Reminiscent"       # Spawn docker container
htb challenge stop                      # Stop running docker (auto-detect)
htb challenge stop "Reminiscent"        # Stop specific challenge docker
htb challenge active                    # Show running docker instance
htb challenge download "Reminiscent"    # Download files
htb challenge download "Reminiscent" -o ./dir/
htb challenge own 'HTB{flag}' -c "Reminiscent"   # Submit flag
htb challenge writeup "Reminiscent"     # Community writeup URL
htb challenge activity "Reminiscent"    # Recent solves
```

### Sherlocks

```bash
htb sherlock list                       # All sherlocks
htb sherlock list --difficulty easy     # Filter by difficulty
htb sherlock list --unsolved            # Unsolved only
htb sherlock categories                 # List categories
htb sherlock info "Meerkat"             # Details
htb sherlock tasks "Meerkat"            # List questions
htb sherlock download "Meerkat"         # Download files
htb sherlock download "Meerkat" -o ./dir/
htb sherlock own "Meerkat" "answer" -t 1     # Submit answer for task 1
htb sherlock progress "Meerkat"         # Your progress
htb sherlock writeup "Meerkat"          # Community writeup info
htb sherlock official-writeup "Meerkat" # Official writeup download URL
```

### VPN

```bash
htb vpn status                          # Current connection status
htb vpn connections                     # All active connections across products
htb vpn servers                         # Labs VPN servers (default)
htb vpn servers --product competitive   # Competitive VPN servers
htb vpn servers --prolab-id 3           # Prolab VPN servers
htb vpn switch 123                      # Switch to server by ID
htb vpn download 123                    # Download TCP config
htb vpn download 123 --udp              # Download UDP config
htb vpn download 123 -o ./file.ovpn     # Save to custom path
```

### Seasons / Arena

```bash
htb season list                         # All seasons
htb season machines                     # Current season machines
htb season machines --season-id 9       # Specific season machines
htb season active-machines              # Currently playable machines
htb season rank                         # Your current season ranking
htb season rank 9                       # Ranking in specific season
htb season leaderboard                  # Top 10 leaderboard
htb season leaderboard -l 20            # Top 20
htb season leaderboard 9 -l 20          # Specific season top 20
htb season own 'flag'                   # Submit arena flag
```

### Dashboard

```bash
htb dashboard favorites                 # Owned/favorited items
htb dashboard inprogress                # In-progress items
htb dashboard recommended               # Recommended for you
```

### Profile

```bash
htb profile basic                       # Your profile
htb profile basic 123456                # Specific user
htb profile badges                      # Your badges
htb profile badges 123456               # User's badges
htb profile activity                    # Your recent solves
htb profile activity 123456             # User's recent solves
htb profile content                     # Your machine solves (default)
htb profile content -t challenge        # Your challenge solves
htb profile content -t sherlock         # Your sherlock solves
```

### Pwnbox

```bash
htb pwnbox status                       # Current Pwnbox state
htb pwnbox start                        # Start Pwnbox (US East)
htb pwnbox start -l eu-west             # Start in specific region
htb pwnbox stop                         # Stop Pwnbox
htb pwnbox usage                        # Usage statistics
```

### Fortresses

```bash
htb fortress list                       # All fortresses
htb fortress info 1                     # Fortress details (by ID)
htb fortress flags 1                    # Flag list (by ID)
htb fortress own 1 'flag_value'         # Submit flag (ID + flag)
htb fortress reset 1                    # Vote to reset (by ID)
```

### Tracks

```bash
htb track list                          # Available tracks
htb track info 1                        # Track details (by ID)
htb track enroll 1                      # Enroll in track (by ID)
htb track like 1                        # Like track (by ID)
```

### Rankings

```bash
htb ranking users                       # Top-ranked users
htb ranking teams                       # Top-ranked teams
htb ranking countries                   # Top-ranked countries
htb ranking universities                # Top-ranked universities
htb ranking country-members "US"        # Members of a country
```

### Teams

```bash
htb team info 7168                      # Team profile (by ID)
htb team members 7168                   # Team members (by ID)
htb team activity 7168                  # Recent team activity (by ID)
```

## JSON Output

Every command supports `--raw` / `-r` for JSON output:

```bash
htb machine active -r | jq '.info.ip'
htb machine list -r | jq '.data[].name'
htb whoami -r | jq '.profile.points'
```

## API Reference

Unofficial HTB API docs: https://gubarz.github.io/unofficial-htb-api/

## License

MIT
