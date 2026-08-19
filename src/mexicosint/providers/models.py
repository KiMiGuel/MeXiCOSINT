"""Stable provider evidence models."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class LocalityEvidence:
    source: str
    kind: str
    query: str
    city: str = ""
    state: str = ""
    country: str = ""
    country_code: str = ""
    formatted_address: str = ""
    latitude: float | None = None
    longitude: float | None = None
    note: str = ""
    raw: dict = field(default_factory=dict)


@dataclass(frozen=True)
class ReputationEvidence:
    source: str
    valid: bool | None = None
    active: bool | None = None
    risk_score: int | None = None
    abuse_recent: bool | None = None
    voip: bool | None = None
    carrier: str = ""
    line_type: str = ""
    country_code: str = ""
    city: str = ""
    region: str = ""
    raw: dict = field(default_factory=dict)
