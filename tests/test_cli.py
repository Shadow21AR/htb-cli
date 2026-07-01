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
        if path == "/v5/virtual_machine/active":
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
        if path == "/v5/virtual_machine/active":
            return {"info": None}
        if path == "/user/info":
            return {"info": {"id": 541515, "name": "me"}}
        raise AssertionError(f"Unexpected path: {path}")

    monkeypatch.setattr(machines_cmd, "api_get", fake_api_get)

    runner = CliRunner()
    result = runner.invoke(app, ["machine", "achievement"])
    assert result.exit_code == 1
    assert "No active machine" in result.output


def test_fortress_list(monkeypatch):
    """`htb fortress list` should display fortresses in a table."""
    from htb.cli import app
    import htb.commands.fortresses as fort_cmd

    runner = CliRunner()

    def fake_api_get(path, params=None):
        assert path == "/fortresses"
        return {
            "status": True,
            "data": [
                {"id": 1, "name": "Jet", "number_of_flags": 11, "owned_flags": 0, "ownership": 0},
                {"id": 2, "name": "Akerva", "number_of_flags": 8, "owned_flags": 0, "ownership": 0},
            ]
        }

    monkeypatch.setattr(fort_cmd, "api_get", fake_api_get)

    result = runner.invoke(app, ["fortress", "list"])
    assert result.exit_code == 0
    assert "Jet" in result.output
    assert "Akerva" in result.output


def test_track_list(monkeypatch):
    """`htb track list` should display tracks in a table."""
    from htb.cli import app
    import htb.commands.tracks as track_cmd

    runner = CliRunner()

    def fake_api_get(path, params=None):
        assert path == "/tracks"
        return [
            {"id": 61, "name": "Test Track", "difficulty": "Easy", "likes": 100, "official": True},
        ]

    monkeypatch.setattr(track_cmd, "api_get", fake_api_get)

    result = runner.invoke(app, ["track", "list"])
    assert result.exit_code == 0
    assert "Test Track" in result.output


def test_ranking_users(monkeypatch):
    """`htb ranking users` should display users."""
    from htb.cli import app
    import htb.commands.rankings as rank_cmd

    runner = CliRunner()

    def fake_api_get(path, params=None):
        assert path == "/rankings/users"
        return {
            "data": [
                {"rank": 1, "name": "TestUser", "country": "US", "points": 1000, "root_owns": 50, "user_owns": 60, "challenge_owns": 70, "fortress": 50},
            ]
        }

    monkeypatch.setattr(rank_cmd, "api_get", fake_api_get)

    result = runner.invoke(app, ["ranking", "users"])
    assert result.exit_code == 0
    assert "TestUser" in result.output


def test_team_info(monkeypatch):
    """`htb team info` should display team details."""
    from htb.cli import app
    import htb.commands.teams as team_cmd

    runner = CliRunner()

    def fake_api_get(path, params=None):
        assert path == "/team/info/1"
        return {"id": 1, "name": "TestTeam", "points": 500, "motto": "we hack"}

    monkeypatch.setattr(team_cmd, "api_get", fake_api_get)

    result = runner.invoke(app, ["team", "info", "1"])
    assert result.exit_code == 0
    assert "TestTeam" in result.output
    assert "we hack" in result.output


def test_sherlock_categories(monkeypatch):
    """`htb sherlock categories` should list categories."""
    from htb.cli import app
    import htb.commands.sherlocks as sh_cmd

    runner = CliRunner()

    def fake_api_get(path, params=None):
        assert path == "/sherlocks/categories/list"
        return {"info": [{"id": 14, "name": "DFIR"}, {"id": 15, "name": "Cloud"}]}

    monkeypatch.setattr(sh_cmd, "api_get", fake_api_get)

    result = runner.invoke(app, ["sherlock", "categories"])
    assert result.exit_code == 0
    assert "DFIR" in result.output
    assert "Cloud" in result.output


def test_test_command_hidden(monkeypatch):
    """`htb` should not show test in help."""
    from htb.cli import app

    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "test" not in result.output


def test_test_command_still_works(monkeypatch):
    """`htb test all` should still work with -y flag."""
    from htb.cli import app
    import htb.commands.test as test_cmd

    runner = CliRunner()

    results_saved = []

    def fake_test(method, path, tag, params=None, post_data=None):
        results_saved.append(tag)

    monkeypatch.setattr(test_cmd, "_test", fake_test)
    monkeypatch.setattr(test_cmd, "RESULTS", [])

    result = runner.invoke(app, ["test", "all", "-y"])
    assert result.exit_code == 0
    assert "Endpoint Scan" in result.output
