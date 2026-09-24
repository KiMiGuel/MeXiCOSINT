"""IPQualityScore phone validation adapter."""

from __future__ import annotations

import aiohttp
import requests

from mexicosint.numbering import NormalizedNumber
from mexicosint.providers.base import Provider
from mexicosint.providers.models import ReputationEvidence
from mexicosint.providers.status import (
    ProviderRequestError,
    ProviderState,
    decode_json_response,
)


def _parse_evidence(data: dict, source: str) -> ReputationEvidence:
    if not isinstance(data, dict) or not any(
        field in data
        for field in (
            "valid",
            "active",
            "fraud_score",
            "recent_abuse",
            "VOIP",
            "carrier",
            "line_type",
        )
    ):
        raise ProviderRequestError(
            ProviderState.INVALID_RESPONSE,
            "IPQualityScore returned an unsupported response schema",
            http_status=200,
        )
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


class IPQualityScoreProvider(Provider[ReputationEvidence]):
    source = "IPQualityScore"

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
        return _parse_evidence(
            decode_json_response(response, "IPQualityScore"),
            self.source,
        )

    async def alookup(self, session: aiohttp.ClientSession, number: NormalizedNumber) -> ReputationEvidence | None:
        if not self.api_key or not number.international_digits:
            return None
        async with session.get(
            self._url(number),
            params={"country": "MX", "strictness": 1},
            timeout=aiohttp.ClientTimeout(total=self.timeout),
        ) as response:
            response.raise_for_status()
            try:
                data = await response.json(content_type=None)
            except (TypeError, ValueError, aiohttp.ContentTypeError) as exc:
                raise ProviderRequestError(
                    ProviderState.INVALID_RESPONSE,
                    "IPQualityScore returned malformed JSON",
                    http_status=response.status,
                ) from exc
        return _parse_evidence(data, self.source)
