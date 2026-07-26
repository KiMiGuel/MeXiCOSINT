"""Geoapify numbering-locality geocoder."""

from __future__ import annotations

from functools import lru_cache

import requests

from mexicosint.providers.models import LocalityEvidence


class GeoapifyProvider:
    source = "Geoapify"

    def __init__(self, api_key: str, timeout: int = 8):
        self.api_key = api_key
        self.timeout = timeout

    @lru_cache(maxsize=256)
    def lookup(self, locality: str) -> LocalityEvidence | None:
        if not self.api_key or not locality:
            return None
        params = {
            "text": locality,
            "filter": "countrycode:mx",
            "format": "geojson",
            "limit": 1,
            "apiKey": self.api_key,
        }
        response = requests.get(
            "https://api.geoapify.com/v1/geocode/search",
            params=params,
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = response.json()
        features = data.get("features") or []
        if not features:
            return None
        props = features[0].get("properties", {})
        return LocalityEvidence(
            source=self.source,
            kind="numbering_locality",
            query=locality,
            city=props.get("city") or props.get("county") or "",
            state=props.get("state") or "",
            country=props.get("country") or "",
            country_code=(props.get("country_code") or "MX").upper(),
            formatted_address=props.get("formatted") or "",
            latitude=props.get("lat"),
            longitude=props.get("lon"),
            note="Numbering locality only; not live phone or subscriber location.",
            raw=props,
        )
