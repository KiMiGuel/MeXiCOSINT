"""Location evidence classification."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache


class EvidenceState(str, Enum):
    """Classification of location evidence quality.

    Mixed in with str (rather than enum.StrEnum, which needs Python 3.11+)
    so it stays a drop-in replacement for the plain strings this used to be:
    transparent equality, f-string formatting, and JSON serialization.
    """
    NO_USABLE_LOCALITY = "no usable locality"
    SINGLE_SOURCE = "single-source result"
    STRONG_AGREEMENT = "strong agreement"
    PARTIAL_AGREEMENT = "partial agreement"
    CONFLICTING_SOURCES = "conflicting sources"

    def __str__(self) -> str:
        return self.value


@dataclass
class SourceVote:
    city: str
    source: str
    weight: float
    extra: str = ""

    @property
    def confidence(self) -> float:
        return self.weight


@dataclass
class EvidenceDecision:
    city: str = ""
    state: EvidenceState = EvidenceState.NO_USABLE_LOCALITY
    sources: list[str] = field(default_factory=list)
    all_sources: list[str] = field(default_factory=list)


CITY_ALIASES = {
    "mexico city": "ciudad de mexico",
    "cdmx": "ciudad de mexico",
    "ciudad de mexico cdmx": "ciudad de mexico",
    "ciudad de mexico": "ciudad de mexico",
    "distrito federal": "ciudad de mexico",
    "nuevo leon": "monterrey",
    "monterrey nuevo leon": "monterrey",
    "jalisco": "guadalajara",
    "guadalajara jalisco": "guadalajara",
    "queretaro queretaro": "queretaro",
    "san luis potosi slp": "san luis potosi",
    "baja california": "tijuana",
    "sinaloa": "culiacan",
    "yucatan": "merida",
    "quintana roo": "cancun",
    "puebla puebla": "puebla",
    "veracruz veracruz": "veracruz",
}


@lru_cache(maxsize=1024)
def normalize_city(city: str) -> str:
    if not city:
        return ""
    city = city.lower().strip()
    city = unicodedata.normalize("NFKD", city).encode("ASCII", "ignore").decode("ASCII")
    city = re.sub(r"[^a-z0-9\s]", " ", city)
    city = re.sub(r"\s+", " ", city).strip()
    return CITY_ALIASES.get(city, city)


def decide_evidence(votes: list[SourceVote]) -> EvidenceDecision:
    usable = [vote for vote in votes if normalize_city(vote.city)]
    if not usable:
        return EvidenceDecision()

    if len(usable) == 1:
        vote = usable[0]
        return EvidenceDecision(
            city=vote.city,
            state=EvidenceState.SINGLE_SOURCE,
            sources=[vote.source],
            all_sources=[vote.source],
        )

    groups = {}
    for vote in usable:
        key = normalize_city(vote.city)
        groups.setdefault(key, {"weight": 0.0, "votes": [], "labels": {}})
        groups[key]["weight"] += vote.weight
        groups[key]["votes"].append(vote)
        groups[key]["labels"][vote.city] = groups[key]["labels"].get(vote.city, 0.0) + vote.weight

    best_key, best = max(groups.items(), key=lambda item: (len(item[1]["votes"]), item[1]["weight"]))
    best_votes = best["votes"]
    best_city = max(best["labels"].items(), key=lambda item: item[1])[0]
    all_sources = [vote.source for vote in usable]

    if len(groups) == 1:
        state = EvidenceState.STRONG_AGREEMENT
    elif len(best_votes) > 1:
        state = EvidenceState.PARTIAL_AGREEMENT
    else:
        state = EvidenceState.CONFLICTING_SOURCES
        best_votes = usable

    return EvidenceDecision(
        city=best_city,
        state=state,
        sources=[vote.source for vote in best_votes],
        all_sources=all_sources,
    )
