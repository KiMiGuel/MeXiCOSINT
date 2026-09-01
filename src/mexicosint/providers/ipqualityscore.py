"""IPQualityScore phone validation adapter."""

from __future__ import annotations

import aiohttp
import requests

from mexicosint.numbering import NormalizedNumber
from mexicosint.providers.models import ReputationEvidence


def _parse_evidence(data: dict, source: str) -> ReputationEvidence:
    return ReputationEvidence(
        source=source,
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


class IPQualityScoreProvider:
    source = "IPQualityScore"

    def __init__(self, api_key: str, timeout: int = 8):
        self.api_key = api_key
        self.timeout = timeout

    def _url(self, number: NormalizedNumber) -> str:
        return f"https://ipqualityscore.com/api/json/phone/{self.api_key}/{number.international_digits}"

    def lookup(self, number: NormalizedNumber) -> ReputationEvidence | None:
        if not self.api_key or not number.international_digits:
            return None
        response = requests.get(
            self._url(number),
            params={"country": "MX", "strictness": 1},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return _parse_evidence(response.json(), self.source)

    async def alookup(self, session: aiohttp.ClientSession, number: NormalizedNumber) -> ReputationEvidence | None:
        if not self.api_key or not number.international_digits:
            return None
        async with session.get(
            self._url(number),
            params={"country": "MX", "strictness": 1},
            timeout=aiohttp.ClientTimeout(total=self.timeout),
        ) as response:
            response.raise_for_status()
            data = await response.json(content_type=None)
        return _parse_evidence(data, self.source)
