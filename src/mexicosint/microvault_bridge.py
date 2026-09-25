"""Strict MicroVault bridge used by MeXiCOSINT.

Normal provider enrichment has exactly one credential source: the
``mexicosint`` profile in MicroVault.  The CLI is queried once with
``--profile mexicosint --json``.  A missing profile, malformed response, or
unavailable vault fails closed; there is no bare vault or per-service
fallback.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum


class VaultConnectState(str, Enum):
    CONNECTED = "connected"
    UNAVAILABLE = "unavailable"
    NON_INTERACTIVE = "non_interactive"
    WRONG_PASSWORD = "wrong_password"
    CORRUPT_VAULT = "corrupt_vault"
    TIMEOUT = "timeout"
    UNKNOWN_ERROR = "unknown_error"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class VaultConnectResult:
    state: VaultConnectState
    mode: str = ""
    detail: str = ""


PROFILE_NAME = "mexicosint"
_PROFILE_COMMAND = ["microvault", "env", "--profile", PROFILE_NAME, "--json"]


def _can_prompt() -> bool:
    try:
        if sys.stdin and sys.stdin.isatty():
            return True
    except (AttributeError, OSError, ValueError):
        pass
    try:
        descriptor = os.open("/dev/tty", os.O_RDWR | os.O_NOCTTY)
    except OSError:
        return False
    os.close(descriptor)
    return True


def _classify_vault_error(detail: str) -> VaultConnectState:
    lowered = detail.lower()
    if any(marker in lowered for marker in (
        "wrong password", "incorrect password", "invalid password",
        "contraseña incorrecta", "password is incorrect",
    )):
        return VaultConnectState.WRONG_PASSWORD
    if any(marker in lowered for marker in (
        "corrupt", "decrypt", "invalid token", "invalid signature", "fernet",
    )):
        return VaultConnectState.CORRUPT_VAULT
    if any(marker in lowered for marker in (
        "inappropriate ioctl", "password input", "end of file", "eoferror",
    )):
        return VaultConnectState.NON_INTERACTIVE
    return VaultConnectState.UNKNOWN_ERROR


def _sanitize_detail(detail: str) -> str:
    """Keep only a short diagnostic and redact common credential shapes."""
    safe = " ".join((detail or "").split())
    safe = re.sub(r"(?i)(api[_-]?key|token|secret|password)\s*[=:]\s*\S+", r"\1=***", safe)
    return safe[:200] or "MicroVault profile request failed"


class MicroVaultBridge:
    """Stateful accessor for the single required MeXiCOSINT profile."""

    def __init__(self):
        self._mode = None
        self._connected = False
        self._available = False
        self._profile = {}
        self.last_connect_result = VaultConnectResult(VaultConnectState.UNAVAILABLE)

    @property
    def is_connected(self) -> bool:
        return self._connected

    def is_available(self) -> bool:
        if self._mode is not None:
            return self._available
        if shutil.which("microvault"):
            self._mode = "cli"
            self._available = True
            return True
        self._available = False
        return False

    def connect_result(self) -> VaultConnectResult:
        if self._connected:
            return VaultConnectResult(VaultConnectState.CONNECTED, self._mode or "")
        if not self.is_available():
            self.last_connect_result = VaultConnectResult(
                VaultConnectState.UNAVAILABLE,
                detail="MicroVault CLI is not available",
            )
            return self.last_connect_result
        if not _can_prompt():
            self.last_connect_result = VaultConnectResult(
                VaultConnectState.NON_INTERACTIVE,
                self._mode or "",
                "MicroVault needs an interactive terminal for its password prompt",
            )
            return self.last_connect_result

        try:
            result = subprocess.run(
                _PROFILE_COMMAND,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=30,
            )
        except subprocess.TimeoutExpired:
            self.last_connect_result = VaultConnectResult(
                VaultConnectState.TIMEOUT, "cli", "MicroVault profile request timed out"
            )
            return self.last_connect_result
        except OSError:
            self.last_connect_result = VaultConnectResult(
                VaultConnectState.UNAVAILABLE, "cli", "MicroVault CLI could not be started"
            )
            return self.last_connect_result

        if result.returncode != 0:
            detail = _sanitize_detail(result.stderr or result.stdout)
            self.last_connect_result = VaultConnectResult(
                _classify_vault_error(detail), "cli", detail
            )
            return self.last_connect_result

        try:
            profile = json.loads(result.stdout)
        except (TypeError, json.JSONDecodeError):
            self.last_connect_result = VaultConnectResult(
                VaultConnectState.UNKNOWN_ERROR,
                "cli",
                "MicroVault returned malformed profile data",
            )
            return self.last_connect_result
        if not isinstance(profile, dict) or not profile:
            self.last_connect_result = VaultConnectResult(
                VaultConnectState.UNKNOWN_ERROR,
                "cli",
                "MicroVault returned an empty profile",
            )
            return self.last_connect_result

        self._profile = {str(service): value for service, value in profile.items()
                          if isinstance(value, str) and value}
        self._connected = True
        self.last_connect_result = VaultConnectResult(VaultConnectState.CONNECTED, "cli")
        return self.last_connect_result

    def connect(self) -> bool:
        return self.connect_result().state == VaultConnectState.CONNECTED

    def get(self, service: str) -> str:
        if not self._connected:
            return ""
        return self._profile.get(service, "")


_bridge = MicroVaultBridge()


def get_bridge() -> MicroVaultBridge:
    return _bridge
