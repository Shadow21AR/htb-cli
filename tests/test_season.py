"""Tests for season commands."""

from typer.testing import CliRunner


def test_season_active_accepts_list_payload(monkeypatch):
    """`htb season active-machines` should not crash if API returns a bare list."""
    from htb.cli import app
    import htb.commands.season as season_cmd

    runner = CliRunner()

    def fake_api_get(path, params=None):
        if path == "/season/machine/active":
            return [
                {
                    "id": 123,
                    "name": "TestMachine",
                    "os": "Linux",
                    "difficultyText": "Easy",
                    "star": 4.2,
                    "free": True,
                }
            ]
        if path == "/v5/virtual_machine/active":
            return {"info": None}
        raise AssertionError(f"Unexpected path: {path}")

    monkeypatch.setattr(season_cmd, "api_get", fake_api_get)

    result = runner.invoke(app, ["season", "active-machines"])
    assert result.exit_code == 0
    assert "TestMachine" in result.output


def test_season_active_accepts_wrapped_payload(monkeypatch):
    """`htb season active-machines` should handle the common {"data": [...]} wrapper."""
    from htb.cli import app
    import htb.commands.season as season_cmd

    runner = CliRunner()

    def fake_api_get(path, params=None):
        if path == "/season/machine/active":
            return {
                "data": [
                    {
                        "id": 456,
                        "name": "WrappedMachine",
                        "os": "Windows",
                        "difficultyText": "Medium",
                        "star": 3.8,
                        "free": False,
                    }
                ]
            }
        if path == "/v5/virtual_machine/active":
            return {"info": None}
        raise AssertionError(f"Unexpected path: {path}")

    monkeypatch.setattr(season_cmd, "api_get", fake_api_get)

    result = runner.invoke(app, ["season", "active-machines"])
    assert result.exit_code == 0
    assert "WrappedMachine" in result.output

