from pathlib import Path

import requests

from mexicosint.core.settings import ScanSettings


def test_settings_create_isolated_sessions():
    first = ScanSettings()
    second = ScanSettings()

    assert isinstance(first.session, requests.Session)
    assert first.session is first.session
    assert first.session is not second.session


def test_settings_manage_output_directories(tmp_path):
    settings = ScanSettings(output_dir=Path(tmp_path))

    assert settings.report_dir == tmp_path / "reports"
    assert settings.map_dir == tmp_path / "maps"
    assert not settings.report_dir.exists()

    settings.ensure_output_dirs()

    assert settings.report_dir.is_dir()
    assert settings.map_dir.is_dir()
    assert settings.get_output_path("result.json") == tmp_path / "result.json"


def test_settings_keep_dummy_and_config_state_isolated(tmp_path):
    config_path = tmp_path / "config.json"
    first = ScanSettings(dummy_mode=True, config_path=config_path)
    second = ScanSettings(dummy_mode=False, config_path=tmp_path / "other.json")

    assert first.dummy_mode is True
    assert second.dummy_mode is False
    assert first.config_path == config_path
    assert second.config_path != config_path
