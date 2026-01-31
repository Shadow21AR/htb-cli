"""
Configuration management for HTB CLI.

Supports multiple token sources:
1. HTB_TOKEN environment variable
2. ~/.htb-token file (plain text, first line)
"""

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Config:
    """HTB CLI configuration."""

    token: str
    api_base: str = "https://labs.hackthebox.com/api"
    api_version: str = "v4"
    timeout: float = 30.0
    max_retries: int = 3

    @property
    def base_url(self) -> str:
        return f"{self.api_base}/{self.api_version}"

    def url(self, path: str) -> str:
        """Build full URL for an endpoint path."""
        # Allow overriding version in path (e.g., "/v5/machine/own")
        # But exclude /vm/ endpoints which are valid v4 endpoints
        if path.startswith("/v") and not path.startswith("/vm/"):
            return f"{self.api_base}{path}"
        return f"{self.base_url}{path}"


def load_token() -> str:
    """Load token from environment or file."""
    # 1. Check environment variable first
    token = os.environ.get("HTB_TOKEN")
    if token:
        return token.strip()

    # 2. Check token file
    token_path = Path.home() / ".htb-token"
    if token_path.exists():
        token = token_path.read_text().strip().split('\n')[0]
        if token:
            return token

    raise FileNotFoundError(
        "No HTB token found.\n"
        "Set HTB_TOKEN environment variable or create ~/.htb-token file:\n"
        "  export HTB_TOKEN='your-token'\n"
        "  # or\n"
        "  echo 'your-token' > ~/.htb-token"
    )


def load_config() -> Config:
    """Load configuration."""
    return Config(token=load_token())


# Global config instance (lazy loaded)
_config: Config | None = None


def get_config() -> Config:
    """Get or load the global config."""
    global _config
    if _config is None:
        _config = load_config()
    return _config
