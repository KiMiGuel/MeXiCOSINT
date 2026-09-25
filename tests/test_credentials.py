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


def test_get_api_key_reads_only_profile_snapshot(monkeypatch):
    monkeypatch.setenv("GEOAPIFY_API_KEY", "generic-env-key")

    assert config.get_api_key({"geoapify": "vault-snapshot"}, "geoapify") == "vault-snapshot"


def test_microvault_cli_requires_profile_and_uses_one_json_fetch(monkeypatch):
    monkeypatch.setattr("mexicosint.microvault_bridge._can_prompt", lambda: True)
    monkeypatch.setattr(
        "mexicosint.microvault_bridge.shutil.which",
        lambda command: "/usr/bin/microvault",
    )

    calls = []
    monkeypatch.setattr(
        "mexicosint.microvault_bridge.subprocess.run",
        lambda cmd, **kwargs: (calls.append(cmd) or Result(
            stdout=json.dumps({"geoapify": "profile-key"})
        )),
    )
    bridge = MicroVaultBridge()

    assert bridge.connect() is True
    assert bridge.get("geoapify") == "profile-key"
    assert calls == [["microvault", "env", "--profile", "mexicosint", "--json"]]


def test_microvault_cli_never_falls_back_to_bare_or_per_service(monkeypatch):
    monkeypatch.setattr("mexicosint.microvault_bridge._can_prompt", lambda: True)
    monkeypatch.setattr(
        "mexicosint.microvault_bridge.shutil.which",
        lambda command: "/usr/bin/microvault",
    )
    calls = []
    monkeypatch.setattr(
        "mexicosint.microvault_bridge.subprocess.run",
        lambda cmd, **kwargs: (calls.append(cmd) or Result(
            returncode=1,
            stderr="profile 'mexicosint' not found",
        )),
    )

    bridge = MicroVaultBridge()

    assert bridge.connect() is False
    assert bridge.get("geoapify") == ""
    assert calls == [["microvault", "env", "--profile", "mexicosint", "--json"]]


def test_microvault_failure_detail_is_sanitized(monkeypatch):
    monkeypatch.setattr("mexicosint.microvault_bridge._can_prompt", lambda: True)
    monkeypatch.setattr(
        "mexicosint.microvault_bridge.shutil.which",
        lambda command: "/usr/bin/microvault",
    )
    monkeypatch.setattr(
        "mexicosint.microvault_bridge.subprocess.run",
        lambda *args, **kwargs: Result(
            returncode=1,
            stderr="failed with api_key=secret-api-key-value",
        ),
    )

    result = MicroVaultBridge().connect_result()

    assert result.state == VaultConnectState.UNKNOWN_ERROR
    assert "secret-api-key-value" not in result.detail
    assert result.detail == "failed with api_key=***"


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
