"""IPQualityScore phone validation adapter."""

from __future__ import annotations

import requests

from mexicosint.numbering import NormalizedNumber
from mexicosint.providers.models import ReputationEvidence


class IPQualityScoreProvider:
    source = "IPQualityScore"

    def __init__(self, api_key: str, timeout: int = 8):
        self.api_key = api_key
        self.timeout = timeout

    def lookup(self, number: NormalizedNumber) -> ReputationEvidence | None:
        if not self.api_key or not number.international_digits:
            return None
        response = requests.get(
            f"https://ipqualityscore.com/api/json/phone/{self.api_key}/{number.international_digits}",
            params={"country": "MX", "strictness": 1},
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = response.json()
        return ReputationEvidence(
            source=self.source,
            valid=data.get("valid"),
            active=data.get("active"),
            risk_score=data.get("fraud_score"),
            abuse_recent=data.get("recent_abuse"),
            voip=data.get("VOIP"),
            carrier=data.get("carrier") or "",
            line_type=data.get("line_type") or "",
            country_code=data.get("country") or "",
            city=data.get("city") or "",
            region=data.get("region") or "",
            raw=data,
        )
