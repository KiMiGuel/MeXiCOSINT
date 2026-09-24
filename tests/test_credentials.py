import json
import sys
import types

import mexicosint.config as config
import mexicosint.main as app
from mexicosint.microvault_bridge import (
    MicroVaultBridge,
    VaultConnectState,
)


class Result:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_get_api_key_precedence_env_then_vault_then_json(monkeypatch):
    monkeypatch.setattr(config, "_from_env", lambda service: "env-key")
    monkeypatch.setattr(config, "_get_from_microvault", lambda service: "vault-key")

    assert config.get_api_key({"geoapify": "json-key"}, "geoapify") == "env-key"

    monkeypatch.setattr(config, "_from_env", lambda service: "")
    assert config.get_api_key({"geoapify": "json-key"}, "geoapify") == "vault-key"

    monkeypatch.setattr(config, "_get_from_microvault", lambda service: "")
    assert config.get_api_key({"geoapify": "json-key"}, "geoapify") == "json-key"


def test_init_config_env_overrides_json_without_microvault(monkeypatch, tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps({"geoapify": "json-key", "numverify": "json-numverify"}),
        encoding="utf-8",
    )
    monkeypatch.setenv("MEXICOSINT_GEOAPIFY_API_KEY", "env-key")
    for name in (
        "MEXICOSINT_NUMVERIFY_API_KEY",
        "NUMVERIFY_API_KEY",
        "MEXICOSINT_OPENCAGE_API_KEY",
        "OPENCAGE_API_KEY",
        "MEXICOSINT_IPQS_API_KEY",
        "IPQUALITYSCORE_API_KEY",
        "IPGS_API_KEY",
        "MEXICOSINT_ABSTRACT_API_KEY",
        "ABSTRACT_PHONE_INTELLIGENCE_API_KEY",
        "ABSTRACT_API_KEY",
    ):
        monkeypatch.delenv(name, raising=False)

    resolved = config.init_config(
        config_path=config_path,
        skip_microvault=True,
    )

    assert resolved["geoapify"] == "env-key"
    assert resolved["numverify"] == "json-numverify"


def test_microvault_cli_profile_uses_one_json_fetch(monkeypatch, tmp_path):
    profiles = tmp_path / "profiles.json"
    profiles.write_text(json.dumps({"mexicosint": ["geoapify"]}), encoding="utf-8")
    monkeypatch.setattr("mexicosint.microvault_bridge._PROFILES_FILE", str(profiles))
    monkeypatch.setattr("mexicosint.microvault_bridge._can_prompt", lambda: True)
    monkeypatch.setattr(
        "mexicosint.microvault_bridge.shutil.which",
        lambda command: "/usr/bin/microvault",
    )

    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return Result(stdout=json.dumps({"geoapify": "profile-key"}))

    monkeypatch.setattr("mexicosint.microvault_bridge.subprocess.run", fake_run)
    bridge = MicroVaultBridge()

    assert bridge.connect() is True
    assert bridge.get("geoapify") == "profile-key"
    assert calls == [
        ["microvault", "env", "--profile", "mexicosint", "--json"]
    ]


def test_microvault_cli_without_profile_fetches_service(monkeypatch, tmp_path):
    profiles = tmp_path / "profiles.json"
    profiles.write_text(json.dumps({}), encoding="utf-8")
    monkeypatch.setattr("mexicosint.microvault_bridge._PROFILES_FILE", str(profiles))
    monkeypatch.setattr("mexicosint.microvault_bridge._can_prompt", lambda: True)
    monkeypatch.setattr(
        "mexicosint.microvault_bridge.shutil.which",
        lambda command: "/usr/bin/microvault",
    )

    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        if cmd == ["microvault", "env"]:
            return Result()
        return Result(stdout="export OPENCAGE_API_KEY='service-key'")

    monkeypatch.setattr("mexicosint.microvault_bridge.subprocess.run", fake_run)
    bridge = MicroVaultBridge()

    assert bridge.connect() is True
    assert bridge.get("opencage_api") == "service-key"
    assert calls == [
        ["microvault", "env"],
        ["microvault", "env", "opencage_api"],
    ]


def test_microvault_python_mode_unlocks_once(monkeypatch):
    vault_module = types.ModuleType("microvault.vault")
    calls = []
    vault_module.list = lambda: calls.append("list")
    vault_module.get = lambda service: calls.append(("get", service)) or "python-key"
    package = types.ModuleType("microvault")
    package.vault = vault_module
    monkeypatch.setitem(sys.modules, "microvault", package)
    monkeypatch.setitem(sys.modules, "microvault.vault", vault_module)
    monkeypatch.setattr("mexicosint.microvault_bridge._can_prompt", lambda: True)

    bridge = MicroVaultBridge()

    assert bridge.is_available() is True
    assert bridge.connect() is True
    assert bridge.get("geoapify") == "python-key"
    assert calls == ["list", ("get", "geoapify")]


def test_sanitize_error_redacts_every_provider_key_shape():
    key = "secret/provider+key"

    assert key not in app._sanitize_error(
        f"https://api.example.test/?api_key={key}", key
    )
    assert "secret%2Fprovider%2Bkey" not in app._sanitize_error(
        "https://api.example.test/?api_key=secret%2Fprovider%2Bkey",
        key,
    )
    assert "***REDACTED***" in app._sanitize_error(f"failed with {key}", key)


def test_microvault_noninteractive_failure_does_not_probe_password(monkeypatch, tmp_path):
    profiles = tmp_path / "profiles.json"
    profiles.write_text(json.dumps({"mexicosint": ["geoapify"]}), encoding="utf-8")
    monkeypatch.setattr("mexicosint.microvault_bridge._PROFILES_FILE", str(profiles))
    monkeypatch.setattr("mexicosint.microvault_bridge._can_prompt", lambda: False)
    monkeypatch.setattr(
        "mexicosint.microvault_bridge.shutil.which",
        lambda command: "/usr/bin/microvault",
    )

    def fail_run(*args, **kwargs):
        raise AssertionError("subprocess must not run without a TTY")

    monkeypatch.setattr("mexicosint.microvault_bridge.subprocess.run", fail_run)
    result = MicroVaultBridge().connect_result()

    assert result.state == VaultConnectState.NON_INTERACTIVE
    assert "interactive terminal" in result.detail


def test_microvault_cli_reports_explicit_wrong_password(monkeypatch, tmp_path):
    profiles = tmp_path / "profiles.json"
    profiles.write_text(json.dumps({}), encoding="utf-8")
    monkeypatch.setattr("mexicosint.microvault_bridge._PROFILES_FILE", str(profiles))
    monkeypatch.setattr("mexicosint.microvault_bridge._can_prompt", lambda: True)
    monkeypatch.setattr(
        "mexicosint.microvault_bridge.shutil.which",
        lambda command: "/usr/bin/microvault",
    )
    monkeypatch.setattr(
        "mexicosint.microvault_bridge.subprocess.run",
        lambda *args, **kwargs: Result(
            returncode=1,
            stderr="Incorrect password",
        ),
    )

    result = MicroVaultBridge().connect_result()

    assert result.state == VaultConnectState.WRONG_PASSWORD


def test_microvault_unknown_failure_does_not_claim_wrong_password(monkeypatch, tmp_path):
    profiles = tmp_path / "profiles.json"
    profiles.write_text(json.dumps({}), encoding="utf-8")
    monkeypatch.setattr("mexicosint.microvault_bridge._PROFILES_FILE", str(profiles))
    monkeypatch.setattr("mexicosint.microvault_bridge._can_prompt", lambda: True)
    monkeypatch.setattr(
        "mexicosint.microvault_bridge.shutil.which",
        lambda command: "/usr/bin/microvault",
    )
    monkeypatch.setattr(
        "mexicosint.microvault_bridge.subprocess.run",
        lambda *args, **kwargs: Result(
            returncode=1,
            stderr="unexpected provider failure",
        ),
    )

    result = MicroVaultBridge().connect_result()

    assert result.state == VaultConnectState.UNKNOWN_ERROR
