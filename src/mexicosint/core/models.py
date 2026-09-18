"""Focused views onto ScanResult's flat fields.

ScanResult (main.py) stays flat: its ~40 fields are read/written from ~150
call sites across main.py, and its flat shape is the live JSON report
format. Rewriting all of that to a nested structure is a large, risky
change with no current consumer to justify it.

These dataclasses give any new code (or future main.py service split) a
typed, focused way to look at a ScanResult without any of that risk:
ScanResult exposes them as read-only properties computed from its existing
fields. Nothing about ScanResult's storage or JSON output changes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class PhoneInfo:
    raw_input: str = ""
    detected_format: str = ""
    international_digits: str = ""
    is_possible: bool = False
    is_mexican: bool = False
    e164: str = ""
    valid: bool = False
    country_code: str = ""
    national_number: str = ""
    region_phonenumbers: str = ""
    lada_region: str = ""


@dataclass(frozen=True)
class IftBlockInfo:
    carrier: str = ""
    modality: str = ""
    zona: str = ""
    fecha_asignacion: str = ""
    service_type: str = ""


@dataclass(frozen=True)
class ApiResponse:
    provider: str
    raw: dict = field(default_factory=dict)
    location: str = ""
    carrier: str = ""
    line_type: str = ""


@dataclass(frozen=True)
class GeocodingResult:
    provider: str
    raw: dict = field(default_factory=dict)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: str = ""


@dataclass(frozen=True)
class ReputationResult:
    provider: str
    raw: dict = field(default_factory=dict)


@dataclass(frozen=True)
class ConsensusResult:
    state: Any = None
    city: str = ""
    confidence: float = 0.0
    sources: list = field(default_factory=list)
    all_votes: list = field(default_factory=list)
