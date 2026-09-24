"""Bridge between MeXiCOSINT and MicroVault.

Tries two approaches to reach MicroVault:
  1. Python import  — works if microvault is installed in the same venv
  2. CLI subprocess — works if `microvault` binary is on $PATH (pipx, global)

The CLI fallback is the common case: pipx isolates MeXiCOSINT in its own
venv, so `from microvault import vault` raises ImportError even when the
user has MicroVault installed globally.

Profile scoping: if a "mexicosint" profile exists in MicroVault
(~/.microvault/profiles.json — see `microvault profile`), the CLI bridge
uses `microvault env --profile mexicosint` instead of bare `microvault
env`, so only MeXiCOSINT's own keys ever cross into this process — not
every key in a vault that may be shared with other tools. profiles.json is
plain JSON (just service names, no key material), so checking for the
profile never needs the master password. Falls back to bare `microvault
env` when the profile hasn't been set up yet.
"""

from __future__ import annotations

import json
import os
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
_PROFILES_FILE = os.path.join(
    os.environ.get("MICROVAULT_HOME", os.path.expanduser("~/.microvault")),
    "profiles.json",
)


def _mexicosint_profile_exists() -> bool:
    try:
        with open(_PROFILES_FILE, encoding="utf-8") as f:
            return PROFILE_NAME in json.load(f)
    except (OSError, json.JSONDecodeError):
        return False


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
    if any(
        marker in lowered
        for marker in (
            "wrong password",
            "incorrect password",
            "invalid password",
            "contraseña incorrecta",
        )
    ):
        return VaultConnectState.WRONG_PASSWORD
    if any(
        marker in lowered
        for marker in (
            "corrupt",
            "decrypt",
            "invalid token",
            "invalid signature",
            "fernet",
        )
    ):
        return VaultConnectState.CORRUPT_VAULT
    if any(
        marker in lowered
        for marker in (
            "inappropriate ioctl",
            "password input",
            "end of file",
            "eoferror",
        )
    ):
        return VaultConnectState.NON_INTERACTIVE
    return VaultConnectState.UNKNOWN_ERROR


class MicroVaultBridge:
    """Lazy, stateful accessor for MicroVault keys.

    Call ``connect()`` once (prompts for password).  After that,
    ``get(service)`` returns the key or "".
    """

    def __init__(self):
        self._mode = None          # "python" | "cli" | None
        self._session = None       # Python API session (mode == "python")
        self._connected = False
        self._available = False
        self._env_cache = None     # {service: key}, populated in CLI mode
        self.last_connect_result = VaultConnectResult(VaultConnectState.UNAVAILABLE)

    # ── detection ──────────────────────────────────────────────────────

    def is_available(self) -> bool:
        """Return True if MicroVault can be reached (import or CLI)."""
        if self._mode is not None:
            return self._available
        # Try Python import first
        try:
            from microvault import vault as _mv  # noqa: F811
            self._session = _mv
            self._mode = "python"
            self._available = True
            return True
        except ImportError:
            pass
        # Try CLI binary
        if shutil.which("microvault"):
            self._mode = "cli"
            self._available = True
            return True
        self._available = False
        return False

    # ── connection (prompts for password) ──────────────────────────────

    def connect_result(self) -> VaultConnectResult:
        """Unlock MicroVault and retain a safe, non-secret failure reason."""
        if self._connected:
            return VaultConnectResult(
                VaultConnectState.CONNECTED,
                self._mode or "",
            )
        if not self.is_available():
            self.last_connect_result = VaultConnectResult(
                VaultConnectState.UNAVAILABLE,
                detail="MicroVault is not installed or importable",
            )
            return self.last_connect_result
        if not _can_prompt():
            self.last_connect_result = VaultConnectResult(
                VaultConnectState.NON_INTERACTIVE,
                self._mode or "",
                "MicroVault needs an interactive terminal for its password prompt",
            )
            return self.last_connect_result

        if self._mode == "python":
            try:
                # Any read triggers the password prompt once. Use list(), not
                # services(), because older MicroVault shadowed that name.
                self._session.list()
                self._connected = True
                self.last_connect_result = VaultConnectResult(
                    VaultConnectState.CONNECTED,
                    "python",
                )
            except Exception as exc:
                self.last_connect_result = VaultConnectResult(
                    _classify_vault_error(f"{type(exc).__name__}: {exc}"),
                    "python",
                    str(exc),
                )
            return self.last_connect_result

        if self._mode == "cli":
            has_profile = _mexicosint_profile_exists()
            cmd = ["microvault", "env"]
            if has_profile:
                cmd += ["--profile", PROFILE_NAME, "--json"]
            try:
                result = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    text=True,
                    timeout=30,
                )
            except subprocess.TimeoutExpired as exc:
                self.last_connect_result = VaultConnectResult(
                    VaultConnectState.TIMEOUT,
                    "cli",
                    str(exc),
                )
                return self.last_connect_result
            except FileNotFoundError as exc:
                self.last_connect_result = VaultConnectResult(
                    VaultConnectState.UNAVAILABLE,
                    "cli",
                    str(exc),
                )
                return self.last_connect_result

            if result.returncode == 0:
                if has_profile:
                    try:
                        self._env_cache = json.loads(result.stdout)
                    except json.JSONDecodeError:
                        self._env_cache = None
                self._connected = True
                self.last_connect_result = VaultConnectResult(
                    VaultConnectState.CONNECTED,
                    "cli",
                )
                return self.last_connect_result

            detail = (result.stderr or result.stdout or "MicroVault connection failed").strip()
            self.last_connect_result = VaultConnectResult(
                _classify_vault_error(detail),
                "cli",
                detail[:300],
            )
            return self.last_connect_result

        self.last_connect_result = VaultConnectResult(
            VaultConnectState.UNKNOWN_ERROR,
            self._mode or "",
        )
        return self.last_connect_result

    def connect(self) -> bool:
        """Compatibility wrapper around :meth:`connect_result`."""
        return self.connect_result().state == VaultConnectState.CONNECTED

    # ── key retrieval ──────────────────────────────────────────────────

    def get(self, service: str) -> str:
        """Return the API key for *service*, or "" if unavailable."""
        if not self._connected:
            return ""

        if self._mode == "python":
            try:
                return self._session.get(service) or ""
            except (KeyError, Exception):
                return ""

        if self._mode == "cli":
            if self._env_cache is not None:
                return self._env_cache.get(service, "")
            try:
                result = subprocess.run(
                    ["microvault", "env", service],
                    stdout=subprocess.PIPE,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0 and result.stdout.strip():
                    # Output is: export SERVICE_API_KEY='value'
                    line = result.stdout.strip()
                    # Extract value after the first = (handles quoted values)
                    _, _, value = line.partition("=")
                    return value.strip("'\"")
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            return ""

        return ""


# Module-level singleton
_bridge = MicroVaultBridge()


def get_bridge() -> MicroVaultBridge:
    return _bridge
