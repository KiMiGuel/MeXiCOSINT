from pathlib import Path

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
