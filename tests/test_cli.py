"""CLI behavior tests."""

from typer.testing import CliRunner


def test_whoami_missing_token_prints_clean_error(tmp_path, monkeypatch):
    """CLI should print a friendly error when no token is available."""
    import htb.config as cfg
    import htb.client as htb_client
    from htb.cli import app

    runner = CliRunner()

    monkeypatch.delenv("HTB_TOKEN", raising=False)
    monkeypatch.setattr(cfg, "keyring", None)
    monkeypatch.setattr(cfg, "user_config_dir", lambda *args, **kwargs: str(tmp_path))

    token_path = cfg.get_token_file_path()
    if token_path.exists():
        token_path.unlink()

    htb_client._client = None

    result = runner.invoke(app, ["whoami"])
    assert result.exit_code == 1
    assert "No HTB token found" in result.output
