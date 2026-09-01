"""Geoapify numbering-locality geocoder."""

from __future__ import annotations

from collections import OrderedDict
from functools import lru_cache

import aiohttp
import requests

from mexicosint.providers.models import LocalityEvidence

_GEOAPIFY_URL = "https://api.geoapify.com/v1/geocode/search"


def _params(api_key: str, locality: str) -> dict:
    return {
        "text": locality,
        "filter": "countrycode:mx",
        "format": "geojson",
        "limit": 1,
        "apiKey": api_key,
    }


def _parse_feature(props: dict, locality: str, source: str) -> LocalityEvidence:
    return LocalityEvidence(
        source=source,
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


class GeoapifyProvider:
    source = "Geoapify"
    _async_cache: OrderedDict = OrderedDict()

    def __init__(self, api_key: str, timeout: int = 8):
        self.api_key = api_key
        self.timeout = timeout

    @lru_cache(maxsize=256)
    def lookup(self, locality: str) -> LocalityEvidence | None:
        if not self.api_key or not locality:
            return None
        response = requests.get(
            _GEOAPIFY_URL,
            params=_params(self.api_key, locality),
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = response.json()
        features = data.get("features") or []
        if not features:
            return None
        return _parse_feature(features[0].get("properties", {}), locality, self.source)

    async def alookup(self, session: aiohttp.ClientSession, locality: str) -> LocalityEvidence | None:
        """Async variant with a small LRU cache keyed by (api_key, locality)."""
        if not self.api_key or not locality:
            return None
        key = (self.api_key, locality)
        cache = self._async_cache
        if key in cache:
            cache.move_to_end(key)
            return cache[key]
        async with session.get(
            _GEOAPIFY_URL,
            params=_params(self.api_key, locality),
            timeout=aiohttp.ClientTimeout(total=self.timeout),
        ) as response:
            response.raise_for_status()
            data = await response.json(content_type=None)
        features = data.get("features") or []
        evidence = None
        if features:
            evidence = _parse_feature(features[0].get("properties", {}), locality, self.source)
        cache[key] = evidence
        if len(cache) > 256:
            cache.popitem(last=False)
        return evidence
