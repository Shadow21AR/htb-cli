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


def test_machine_achievement_missing_token_prints_clean_error(tmp_path, monkeypatch):
    """Command should print a friendly error when no token is available."""
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

    result = runner.invoke(app, ["machine", "achievement", "Gavel"])
    assert result.exit_code == 1
    assert "No HTB token found" in result.output


def test_machine_achievement_uses_active_machine_when_name_omitted(monkeypatch):
    from htb.cli import app
    import htb.commands.machines as machines_cmd

    def fake_api_get(path, params=None):
        if path == "/machine/active":
            return {"info": {"id": 832, "name": "Gavel"}}
        if path == "/user/info":
            return {"info": {"id": 541515, "name": "me"}}
        raise AssertionError(f"Unexpected path: {path}")

    monkeypatch.setattr(machines_cmd, "api_get", fake_api_get)

    runner = CliRunner()
    result = runner.invoke(app, ["machine", "achievement"])
    assert result.exit_code == 0
    assert "https://labs.hackthebox.com/achievement/machine/541515/832" in result.output


def test_machine_achievement_no_active_machine(monkeypatch):
    from htb.cli import app
    import htb.commands.machines as machines_cmd

    def fake_api_get(path, params=None):
        if path == "/machine/active":
            return {"info": None}
        if path == "/user/info":
            return {"info": {"id": 541515, "name": "me"}}
        raise AssertionError(f"Unexpected path: {path}")

    monkeypatch.setattr(machines_cmd, "api_get", fake_api_get)

    runner = CliRunner()
    result = runner.invoke(app, ["machine", "achievement"])
    assert result.exit_code == 1
    assert "No active machine" in result.output
