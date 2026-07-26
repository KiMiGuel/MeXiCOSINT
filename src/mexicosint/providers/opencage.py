"""OpenCage numbering-locality geocoder."""

from __future__ import annotations

from functools import lru_cache

import requests

from mexicosint.providers.models import LocalityEvidence


class OpenCageProvider:
    source = "OpenCage"

    def __init__(self, api_key: str, timeout: int = 8):
        self.api_key = api_key
        self.timeout = timeout

    @lru_cache(maxsize=256)
    def lookup(self, locality: str) -> LocalityEvidence | None:
        if not self.api_key or not locality:
            return None
        params = {
            "q": locality,
            "key": self.api_key,
            "countrycode": "mx",
            "limit": 1,
            "language": "es",
            "no_annotations": 1,
        }
        response = requests.get(
            "https://api.opencagedata.com/geocode/v1/json",
            params=params,
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = response.json()
        results = data.get("results") or []
        if not results:
            return None
        item = results[0]
        components = item.get("components") or {}
        geometry = item.get("geometry") or {}
        return LocalityEvidence(
            source=self.source,
            kind="numbering_locality",
            query=locality,
            city=(
                components.get("city")
                or components.get("town")
                or components.get("village")
                or components.get("municipality")
                or components.get("county")
                or ""
            ),
            state=components.get("state") or "",
            country=components.get("country") or "",
            country_code=(components.get("country_code") or "mx").upper(),
            formatted_address=item.get("formatted") or "",
            latitude=geometry.get("lat"),
            longitude=geometry.get("lng"),
            note="Numbering locality only; not live phone or subscriber location.",
            raw=item,
        )
