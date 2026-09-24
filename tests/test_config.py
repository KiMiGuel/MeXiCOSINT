from pathlib import Path

from mexicosint.cli import main as cli_main
import mexicosint.config as config
import mexicosint.main as app


def test_dummy_config_ignores_existing_disk_config(monkeypatch, tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text('{"legacy_one": "old", "legacy_two": "old"}', encoding="utf-8")
    settings = app.ScanSettings(
        dummy_mode=True,
        config_path=Path(config_path),
    )

    config = app.init_config(settings=settings)

    assert "geoapify" in config
    assert "ipqualityscore" in config
    assert "legacy_one" not in config
    assert "legacy_two" not in config


def test_all_environment_credentials_skip_microvault_auto_connect(monkeypatch, tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text("{}", encoding="utf-8")
    env_names = {
        "abstract_phone_intelligence": "ABSTRACT_API_KEY",
        "numverify": "NUMVERIFY_API_KEY",
        "opencage": "OPENCAGE_API_KEY",
        "geoapify": "GEOAPIFY_API_KEY",
        "ipqualityscore": "IPGS_API_KEY",
    }
    for service, name in env_names.items():
        monkeypatch.setenv(name, f"env-{service}")

    class AvailableBridge:
        _connected = False
        _available = True

    connect_calls = []
    monkeypatch.setattr("mexicosint.config._get_microvault_bridge", lambda: AvailableBridge())
    monkeypatch.setattr(
        "mexicosint.config.connect_microvault",
        lambda: connect_calls.append(True) or False,
    )

    resolved = app.init_config(
        settings=app.ScanSettings(config_path=Path(config_path))
    )

    assert connect_calls == []
    assert resolved == {service: f"env-{service}" for service in env_names}


def test_legacy_abstract_alias_reports_json_source(monkeypatch):
    monkeypatch.setattr("mexicosint.config._from_env", lambda service: "")
    monkeypatch.setattr("mexicosint.config._get_from_microvault", lambda service: "")

    source = config.get_credential_source(
        "abstract_phone_intelligence",
        {"abstract": "legacy-key"},
    )

    assert source == "json"


def test_cli_set_key_preserves_canonical_provider_workflow(monkeypatch, tmp_path, capsys):
    config_path = tmp_path / "config.json"
    monkeypatch.setattr(app, "CONFIG_PATH", Path(config_path))

    assert cli_main(["--set-key", "ipqualityscore", "test_key_value"]) == 0
    assert config_path.stat().st_mode & 0o777 == 0o600

    saved = config_path.read_text(encoding="utf-8")
    assert '"ipqualityscore": "test_key_value"' in saved

    assert cli_main(["--list-keys"]) == 0
    listed = capsys.readouterr().out
    assert "ipqualityscore" in listed
    assert "test_key_value" not in listed
