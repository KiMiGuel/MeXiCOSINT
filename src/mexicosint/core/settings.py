"""Runtime settings and resources for a MeXiCOSINT scan."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

import requests

if TYPE_CHECKING:
    from mexicosint.providers.models import LocalityEvidence


@dataclass
class ScanSettings:
    """Per-scan configuration and injectable runtime resources.

    The settings object is created by the CLI entry point and passed through the
    scan pipeline. It deliberately replaces mutable module globals so concurrent
    or repeated scans cannot change one another's mode, output location, or HTTP
    session.
    """

    dummy_mode: bool = False
    output_dir: Path = field(default_factory=lambda: Path("output"))
    default_timeout: float = 15
    _session: requests.Session | None = field(default=None, repr=False)
    nominatim_cache: dict[str, LocalityEvidence | None] = field(
        default_factory=dict, repr=False
    )

    @property
    def report_dir(self) -> Path:
        return self.output_dir / "reports"

    @property
    def map_dir(self) -> Path:
        return self.output_dir / "maps"

    @property
    def session(self) -> requests.Session:
        """Return this scan's lazy, shared synchronous HTTP session."""
        if self._session is None:
            self._session = requests.Session()
        return self._session

    def ensure_output_dirs(self) -> None:
        """Create output directories only when a report or map is written."""
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.map_dir.mkdir(parents=True, exist_ok=True)

    def get_output_path(self, filename: str) -> Path:
        return self.output_dir / filename
