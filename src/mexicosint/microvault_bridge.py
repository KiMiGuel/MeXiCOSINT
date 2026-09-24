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
                                    # when a profile fetch batches every key
                                    # in one call instead of one per service

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

    def connect(self) -> bool:
        """Unlock / verify MicroVault.  Returns True on success."""
        if self._connected:
            return True
        if not self.is_available():
            return False

        if self._mode == "python":
            try:
                # Any read triggers the password prompt once.
                # Use list() (not services(), which is shadowed by the module's
                # own list() function in microvault <fixed>).
                self._session.list()
                self._connected = True
                return True
            except (FileNotFoundError, PermissionError, Exception):
                return False

        if self._mode == "cli":
            # `microvault env` prompts for the password, then prints
            # `export NAME=value` lines for every stored service.  Exit code 0
            # means the password was accepted.  Used purely as a connection test.
            #
            # When a "mexicosint" profile exists, fetch it as JSON in this
            # same call instead: one password prompt gets every key this run
            # will need, cached by vault-native service name, so get() below
            # never has to shell out (and re-prompt) again per service. Keys
            # for other tools sharing the vault still never cross into this
            # process either way.
            has_profile = _mexicosint_profile_exists()
            cmd = ["microvault", "env"]
            if has_profile:
                cmd += ["--profile", PROFILE_NAME, "--json"]
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True, text=True, timeout=30,
                )
                if result.returncode == 0:
                    if has_profile:
                        try:
                            self._env_cache = json.loads(result.stdout)
                        except json.JSONDecodeError:
                            self._env_cache = None
                    self._connected = True
                    return True
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            return False

        return False

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
                    capture_output=True, text=True, timeout=10,
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
