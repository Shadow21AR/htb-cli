# HTB CLI

Clean, modular command-line interface for the Hack The Box API.

## Features

- **Machines** — List, spawn by name/ID, stop, reset, submit flags, todo list, writeups
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
htb status        # User, connection, active machine
htb whoami        # Your profile with level, XP, streak
htb search linux  # Global search
```

### Auth

```bash
htb auth set      # Store token
htb auth show     # Show token source (never reveals token)
htb auth status   # Validate token + show user info
htb auth unset    # Remove stored token
```

### Machines

```bash
htb machine list                         # Active machines
htb machine list --retired               # Retired machines
htb machine list --difficulty easy       # Filter by difficulty
htb machine list --sort name             # Sort by name
htb machine list --search "gavel"        # Search by name
htb machine info Gavel                   # Detailed info
htb machine spawn Gavel                  # Spawn by name
htb machine spawn 811                    # Spawn by ID
htb machine active                       # Current spawned machine
htb machine stop                         # Terminate
htb machine reset                        # Reset
htb machine own 'HTB{flag}'             # Submit flag
htb machine todo                         # Your todo list
htb machine add-todo Gavel               # Toggle todo
htb machine writeup Gavel                # Official writeup (VIP)
htb machine achievement Gavel            # Shareable URL
htb machine unreleased                   # Upcoming machines
```

### Challenges

```bash
htb challenge list                       # Active challenges
htb challenge list --category web        # Filter by category
htb challenge list --difficulty easy     # Filter by difficulty
htb challenge list --unsolved            # Unsolved only
htb challenge list --retired             # Retired challenges
htb challenge categories                 # List categories
htb challenge info "Reminiscent"         # Detailed info
htb challenge start "Reminiscent"        # Spawn docker
htb challenge stop "Reminiscent"         # Stop docker
htb challenge active                     # Running docker
htb challenge download "Reminiscent"     # Download files
htb challenge download "Reminiscent" -o ./downloads/
htb challenge own 'HTB{flag}' --challenge "Reminiscent"
htb challenge writeup "Reminiscent"      # Community writeups
htb challenge activity "Reminiscent"     # Recent solves
```

### Sherlocks

```bash
htb sherlock list                        # List investigations
htb sherlock categories                  # List categories
htb sherlock info "Meerkat"              # Detailed info
htb sherlock tasks "Meerkat"             # List questions
htb sherlock download "Meerkat"          # Download files
htb sherlock own "Meerkat" "answer" --task 1
htb sherlock progress "Meerkat"          # Your progress
htb sherlock writeup "Meerkat"           # Community writeups
htb sherlock official-writeup "Meerkat"  # Official writeup URL
```

### VPN

```bash
htb vpn status                           # Current connection
htb vpn status labs                      # Labs connection status
htb vpn status competitive               # Competitive status
htb vpn connections                      # All active connections
htb vpn servers                          # Labs VPN servers
htb vpn servers --product competitive    # Competitive servers
htb vpn servers --prolab-id 3            # Prolab servers
htb vpn switch 123                       # Switch server
htb vpn download 123                     # TCP config
htb vpn download 123 --udp               # UDP config
htb vpn download 123 -o ./downloads/
```

### Seasons / Arena

```bash
htb season list                          # All seasons
htb season machines                      # Season machines
htb season active-machines               # Currently playable
htb season rank                          # Your current rank
htb season rank 9                        # Specific season
htb season leaderboard --limit 20        # Top players
htb season leaderboard 9 --limit 10      # Specific season
htb season own 'flag'                    # Submit arena flag
```

### Dashboard

```bash
htb dashboard favorites                  # Owned/favorited items
htb dashboard inprogress                 # In-progress items
htb dashboard recommended                # Recommended for you
```

### Profile

```bash
htb profile basic                        # Your profile
htb profile basic 123456                 # Specific user
htb profile badges                       # Your badges
htb profile badges 123456                # User's badges
htb profile activity                     # Recent solves
htb profile activity 123456
htb profile content                      # Solves by type
htb profile content 123456
```

### Pwnbox

```bash
htb pwnbox status                        # Current state
htb pwnbox start                         # Start instance
htb pwnbox stop                          # Stop instance
htb pwnbox usage                         # Usage statistics
```

### Fortresses

```bash
htb fortress list                        # All fortresses
htb fortress info "Jet"                  # Detailed info
htb fortress flags "Jet"                 # Flag list
htb fortress own 'flag'                  # Submit flag
htb fortress reset "Jet"                 # Vote to reset
```

### Tracks

```bash
htb track list                           # Available tracks
htb track info "TrackName"               # Detailed info
htb track enroll "TrackName"             # Enroll
htb track like "TrackName"               # Like
```

### Rankings

```bash
htb ranking users                        # Top users
htb ranking users --limit 50
htb ranking teams                        # Top teams
htb ranking countries                    # Top countries
htb ranking universities                 # Top universities
htb ranking country-members "US"         # Country members
```

### Teams

```bash
htb team info                            # Your team
htb team info 7168                       # Specific team
htb team members                         # Your team members
htb team members 7168                    # Team's members
htb team activity                        # Recent team activity
htb team activity 7168
```

## JSON Output

Every command supports `--raw` / `-r` for JSON output:

```bash
htb machine active -r | jq '.info.ip'
htb machine list -r | jq '.data[].name'
IP=$(htb machine active -r | jq -r '.info.ip')
nmap -sV $IP
```

## API Reference

Unofficial HTB API docs: https://gubarz.github.io/unofficial-htb-api/

## License

MIT
