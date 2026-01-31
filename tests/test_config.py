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
