"""
Configuration management for HTB CLI.

Supports multiple token sources:
1. HTB_TOKEN environment variable
2. OS keyring (optional)
3. XDG config file (plain text, first line)
"""

import os
from os import chmod
from dataclasses import dataclass
from pathlib import Path

from platformdirs import user_config_dir

try:
    import keyring
except Exception:  # pragma: no cover - optional dependency
    keyring = None

KEYRING_SERVICE = "htb-cli"
KEYRING_USER = "token"

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
    token, _ = resolve_token()
    return token


def resolve_token() -> tuple[str, str]:
    """Resolve token and return (token, source)."""
    # 1. Check environment variable first
    token = os.environ.get("HTB_TOKEN")
    if token:
        return token.strip(), "env"

    # 2. Check keyring
    if keyring is not None:
        try:
            token = keyring.get_password(KEYRING_SERVICE, KEYRING_USER)
            if token:
                return token.strip(), "keyring"
        except Exception:
            pass

    # 3. Check token file
    token_path = get_token_file_path()
    if token_path.exists():
        token = token_path.read_text().strip().split("\n")[0]
        if token:
            return token, "file"

    raise FileNotFoundError(
        "No HTB token found.\n"
        "Set HTB_TOKEN environment variable or run:\n"
        "  htb auth set"
    )


def get_token_source() -> str | None:
    """Return the current token source (env, keyring, file) if available."""
    try:
        _, source = resolve_token()
        return source
    except FileNotFoundError:
        return None


def get_token_file_path() -> Path:
    """Return the token file path (XDG config)."""
    config_dir = Path(user_config_dir("htb-cli", "htb"))
    return config_dir / "token"


def set_token(token: str) -> str:
    """Persist token to keyring if available, otherwise config file."""
    if not token or not token.strip():
        raise ValueError("Token cannot be empty")

    token = token.strip()

    if keyring is not None:
        try:
            keyring.set_password(KEYRING_SERVICE, KEYRING_USER, token)
            return "keyring"
        except Exception:
            pass

    token_path = get_token_file_path()
    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(token + "\n")
    chmod(token_path, 0o600)
    return "file"


def unset_token() -> dict[str, bool]:
    """Remove token from keyring and config file."""
    removed = {"keyring": False, "file": False}

    if keyring is not None:
        try:
            keyring.delete_password(KEYRING_SERVICE, KEYRING_USER)
            removed["keyring"] = True
        except Exception:
            pass

    token_path = get_token_file_path()
    if token_path.exists():
        token_path.unlink()
        removed["file"] = True

    return removed


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
