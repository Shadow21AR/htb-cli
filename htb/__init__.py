"""
HTB CLI - Command Line Interface for Hack The Box.

A clean, modular Python CLI for the HTB API.
"""

import re
from pathlib import Path

try:
    _src = Path(__file__).parent.parent.joinpath("pyproject.toml").read_text()
    _m = re.search(r'^version\s*=\s*"([^"]+)"', _src, re.MULTILINE)
    __version__ = _m.group(1) if _m else "dev"
except Exception:
    __version__ = "dev"
