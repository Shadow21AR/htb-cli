"""Tests for configuration module."""

import os
from unittest.mock import patch


def test_config_from_env():
    """Test loading token from environment variable."""
    with patch.dict(os.environ, {"HTB_TOKEN": "test-token"}):
        from htb.config import load_token
        # Force reload
        token = load_token()
        assert token == "test-token"


def test_config_dataclass():
    """Test Config dataclass."""
    from htb.config import Config

    config = Config(token="test")
    assert config.token == "test"
    assert config.api_base == "https://labs.hackthebox.com/api"
    assert config.api_version == "v4"


def test_config_url_building():
    """Test URL building."""
    from htb.config import Config

    config = Config(token="test")

    # Standard path
    assert config.url("/machine/list") == "https://labs.hackthebox.com/api/v4/machine/list"

    # Version override
    assert config.url("/v5/machine/own") == "https://labs.hackthebox.com/api/v5/machine/own"


def test_config_from_file(tmp_path, monkeypatch):
    """Test loading token from config file when env/keyring are absent."""
    from htb import config as cfg

    # Force no env token and no keyring
    monkeypatch.delenv("HTB_TOKEN", raising=False)
    monkeypatch.setattr(cfg, "keyring", None)

    # Redirect config dir to tmp
    monkeypatch.setattr(cfg, "user_config_dir", lambda *args, **kwargs: str(tmp_path))

    token_path = cfg.get_token_file_path()
    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text("file-token\n")

    token = cfg.load_token()
    assert token == "file-token"


def test_missing_token_raises_htb_error(tmp_path, monkeypatch):
    """Ensure missing token raises HTBError (not FileNotFoundError)."""
    from htb import client as htb_client
    from htb import config as cfg

    # Force no env token and no keyring
    monkeypatch.delenv("HTB_TOKEN", raising=False)
    monkeypatch.setattr(cfg, "keyring", None)
    monkeypatch.setattr(cfg, "user_config_dir", lambda *args, **kwargs: str(tmp_path))

    # Ensure no token file
    token_path = cfg.get_token_file_path()
    if token_path.exists():
        token_path.unlink()

    htb_client._client = None
    cfg._config = None

    try:
        htb_client.get_client()
        assert False, "Expected HTBError"
    except htb_client.HTBError as e:
        assert "No HTB token found" in str(e)
