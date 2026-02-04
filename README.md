# HTB CLI

A clean, modular command-line interface for the Hack The Box Labs API.

## Features

- **Machines**: List, spawn (by name!), stop, reset, submit flags, todo list, writeups
- **Challenges**: Browse, start docker containers, download files, submit flags
- **Sherlocks**: DFIR investigation challenges with multi-task support
- **VPN**: Manage VPN connections and download configs
- **Seasons**: Arena/competitive season support
- **Search**: Global search across machines, challenges, and users

## Installation

```bash
pipx install htb-terminal
```

To enable OS keyring storage:

```bash
pipx install "htb-terminal[auth]"
```

If a keyring backend isn’t available on your system, the CLI automatically falls back to the
config file token at `~/.config/htb-cli/token`.

Check if keyring is installed:

```bash
python -c "import keyring; print(keyring.__version__)"
```

If you already installed `htb-terminal` without extras:

```bash
pipx inject htb-terminal keyring
```

## Setup

Get your API token from [HTB App Token Settings](https://app.hackthebox.com/account-settings).

```bash
# Recommended: store token securely (keyring if available)
htb auth set

# Option 2: Environment variable (overrides stored token)
export HTB_TOKEN='your-token-here'  # add to ~/.bashrc to persist
```

If keyring is unavailable, the token is stored in `~/.config/htb-cli/token` with mode `0600`.

## Usage

```bash
# Quick status
htb status
htb whoami
htb search "linux"

# Auth
htb auth set
htb auth show
htb auth status
htb auth unset

# Machines (supports name or ID!)
htb machine list
htb machine list --retired
htb machine list --difficulty easy
htb machine list --sort name
htb machine list --search "gavel"
htb machine info Gavel
htb machine info 811
htb machine spawn Gavel              # By name
htb machine spawn 811                # By ID
htb machine active
htb machine stop
htb machine reset
htb machine own 'flag'
htb machine unreleased
htb machine todo                     # Your todo list
htb machine add-todo Gavel           # Toggle todo (add/remove)
htb machine writeup Gavel            # Official writeup (VIP)

# Challenges
htb challenge list
htb challenge list --category web
htb challenge list --difficulty easy
htb challenge list --category forensics --difficulty easy --unsolved
htb challenge list --retired
htb challenge categories
htb challenge info "Reminiscent"
htb challenge active                 # Show running docker instance
htb challenge start "Reminiscent"
htb challenge stop "Reminiscent"
htb challenge download "Reminiscent"
htb challenge download "Reminiscent" -o ./downloads/
htb challenge own 'HTB{flag}' --challenge "Reminiscent"

# Sherlocks
htb sherlock list
htb sherlock info "Meerkat"
htb sherlock tasks "Meerkat"         # List questions
htb sherlock download "Meerkat"
htb sherlock download "Meerkat" -o ./downloads/
htb sherlock own "Meerkat" "answer" --task 1

# VPN
htb vpn status
htb vpn status labs
htb vpn status competitive
htb vpn connections
htb vpn servers                      # Defaults to labs
htb vpn servers --product competitive
htb vpn servers --product starting_point
htb vpn switch 123
htb vpn download 123                 # TCP by default
htb vpn download 123 --udp           # UDP variant
htb vpn download 123 -o ./downloads/

# Seasons/Arena
htb season list
htb season machines
htb season active
htb season rank                      # Current season
htb season rank 9                    # Specific season
htb season leaderboard --limit 20
htb season leaderboard 9 --limit 10
htb season own 'flag'
```

## JSON Output

All commands support `--raw` / `-r` flag for JSON output:

```bash
# Get machine IP
htb machine active -r | jq '.info.ip'

# List machine names
htb machine list -r | jq '.data[].name'

# Script example
IP=$(htb machine active -r | jq -r '.info.ip')
nmap -sV $IP
```

## API Reference

Full API docs: https://gubarz.github.io/unofficial-htb-api/ 

## License

MIT
