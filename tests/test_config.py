import mexicosint.config as config
import mexicosint.main as app


def test_dummy_config_is_in_memory_and_has_no_file_dependency(tmp_path):
    settings = app.ScanSettings(dummy_mode=True)

    resolved = app.init_config(settings=settings)

    assert resolved == {service: f"dummy_key_{service}" for service in app.SAMPLE_CONFIG}
    assert not list(tmp_path.iterdir())


def test_normal_config_uses_only_microvault_profile(monkeypatch):
    class Bridge:
        _connected = True

        def is_available(self):
            return True

        def connect_result(self):
            class Result:
                state = type("State", (), {"value": "connected"})()
            return Result()

        def is_connected(self):
            return True

    monkeypatch.setattr(config, "_get_microvault_bridge", lambda: Bridge())
    monkeypatch.setattr(config, "_get_from_microvault", lambda service: {
        "geoapify": "vault-key",
    }.get(service, ""))

    assert config.init_config() == {"geoapify": "vault-key"}


def test_legacy_abstract_alias_is_not_a_plaintext_source(monkeypatch):
    monkeypatch.setattr(config, "_get_from_microvault", lambda service: "")

    assert config.get_credential_source(
        "abstract_phone_intelligence",
        {"abstract": "legacy-key"},
    ) == "missing"


def test_normal_config_ignores_environment_and_json(tmp_path, monkeypatch):
    config_file = tmp_path / "config.json"
    config_file.write_text('{"geoapify": "json-key"}', encoding="utf-8")
    monkeypatch.setenv("GEOAPIFY_API_KEY", "env-key")

    assert config.init_config() == {}
    assert config.get_api_key({"geoapify": "json-key"}, "geoapify") == "json-key"
    assert config.get_credential_source("geoapify", {"geoapify": "json-key"}) == "microvault"
    assert config_file.read_text(encoding="utf-8") == '{"geoapify": "json-key"}'
