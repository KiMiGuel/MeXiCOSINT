"""OpenCage numbering-locality geocoder."""

from __future__ import annotations

from collections import OrderedDict
from functools import lru_cache

import aiohttp
import requests

from mexicosint.providers.models import LocalityEvidence

_OPENCAGE_URL = "https://api.opencagedata.com/geocode/v1/json"


def _params(api_key: str, locality: str) -> dict:
    return {
        "q": locality,
        "key": api_key,
        "countrycode": "mx",
        "limit": 1,
        "language": "es",
        "no_annotations": 1,
    }


def _parse_item(item: dict, locality: str, source: str) -> LocalityEvidence:
    components = item.get("components") or {}
    geometry = item.get("geometry") or {}
    return LocalityEvidence(
        source=source,
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


class OpenCageProvider:
    source = "OpenCage"
    _async_cache: OrderedDict = OrderedDict()

    def __init__(self, api_key: str, timeout: int = 8):
        self.api_key = api_key
        self.timeout = timeout

    @lru_cache(maxsize=256)
    def lookup(self, locality: str) -> LocalityEvidence | None:
        if not self.api_key or not locality:
            return None
        response = requests.get(
            _OPENCAGE_URL,
            params=_params(self.api_key, locality),
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = response.json()
        results = data.get("results") or []
        if not results:
            return None
        return _parse_item(results[0], locality, self.source)

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
            _OPENCAGE_URL,
            params=_params(self.api_key, locality),
            timeout=aiohttp.ClientTimeout(total=self.timeout),
        ) as response:
            response.raise_for_status()
            data = await response.json(content_type=None)
        results = data.get("results") or []
        evidence = None
        if results:
            evidence = _parse_item(results[0], locality, self.source)
        cache[key] = evidence
        if len(cache) > 256:
            cache.popitem(last=False)
        return evidence
