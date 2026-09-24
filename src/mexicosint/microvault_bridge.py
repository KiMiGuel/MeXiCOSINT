"""Bridge between MeXiCOSINT and MicroVault.

Tries two approaches to reach MicroVault:
  1. Python import  — works if microvault is installed in the same venv
  2. CLI subprocess — works if `microvault` binary is on $PATH (pipx, global)

The CLI fallback is the common case: pipx isolates MeXiCOSINT in its own
venv, so `from microvault import vault` raises ImportError even when the
user has MicroVault installed globally.
"""

from __future__ import annotations

import shutil
import subprocess


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
            # `microvault env` (no arg) prompts for the password, then prints
            # `export NAME=value` lines for every stored service.  Exit code 0
            # means the password was accepted.  Used purely as a connection test.
            try:
                result = subprocess.run(
                    ["microvault", "env"],
                    capture_output=True, text=True, timeout=30,
                )
                if result.returncode == 0:
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
