from pathlib import Path

from mexicosint.cli import main as cli_main
import mexicosint.main as app


def test_dummy_config_ignores_existing_disk_config(monkeypatch, tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text('{"legacy_one": "old", "legacy_two": "old"}', encoding="utf-8")
    monkeypatch.setattr(app, "CONFIG_PATH", Path(config_path))
    monkeypatch.setattr(app, "DUMMY_MODE", True)

    config = app.init_config()

    assert "geoapify" in config
    assert "google_places" in config
    assert "ipqualityscore" in config
    assert "legacy_one" not in config
    assert "legacy_two" not in config


def test_cli_set_key_preserves_canonical_provider_workflow(monkeypatch, tmp_path, capsys):
    config_path = tmp_path / "config.json"
    monkeypatch.setattr(app, "CONFIG_PATH", Path(config_path))

    assert cli_main(["--set-key", "google_places", "test_key_value"]) == 0
    assert config_path.stat().st_mode & 0o777 == 0o600

    saved = config_path.read_text(encoding="utf-8")
    assert '"google_places": "test_key_value"' in saved

    assert cli_main(["--list-keys"]) == 0
    listed = capsys.readouterr().out
    assert "google_places" in listed
    assert "test_key_value" not in listed
