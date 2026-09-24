"""Geoapify numbering-locality geocoder."""

from __future__ import annotations

from collections import OrderedDict
from functools import lru_cache

import aiohttp
import requests

from mexicosint.providers.base import Provider
from mexicosint.providers.models import LocalityEvidence
from mexicosint.providers.status import (
    ProviderRequestError,
    ProviderState,
    decode_json_response,
)

_GEOAPIFY_URL = "https://api.geoapify.com/v1/geocode/search"


def _params(api_key: str, locality: str) -> dict:
    return {
        "text": locality,
        "filter": "countrycode:mx",
        "format": "geojson",
        "limit": 1,
        "apiKey": api_key,
    }


def _features(data) -> list:
    if not isinstance(data, dict) or not isinstance(data.get("features"), list):
        raise ProviderRequestError(
            ProviderState.INVALID_RESPONSE,
            "Geoapify returned an unsupported response schema",
            http_status=200,
        )
    return data["features"]


def _parse_feature(props: dict, locality: str, source: str) -> LocalityEvidence:
    try:
        latitude = float(props["lat"])
        longitude = float(props["lon"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ProviderRequestError(
            ProviderState.INVALID_RESPONSE,
            "Geoapify result is missing usable coordinates",
            http_status=200,
        ) from exc
    return LocalityEvidence(
        source=source,
        kind="numbering_locality",
        query=locality,
        city=props.get("city") or props.get("county") or "",
        state=props.get("state") or "",
        country=props.get("country") or "",
        country_code=(props.get("country_code") or "MX").upper(),
        formatted_address=props.get("formatted") or "",
        latitude=latitude,
        longitude=longitude,
        note="Numbering locality only; not live phone or subscriber location.",
        raw=props,
    )


class GeoapifyProvider(Provider[LocalityEvidence]):
    source = "Geoapify"
    _async_cache: OrderedDict = OrderedDict()

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
        data = decode_json_response(response, "Geoapify")
        features = _features(data)
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
            try:
                data = await response.json(content_type=None)
            except (TypeError, ValueError, aiohttp.ContentTypeError) as exc:
                raise ProviderRequestError(
                    ProviderState.INVALID_RESPONSE,
                    "Geoapify returned malformed JSON",
                    http_status=response.status,
                ) from exc
        features = _features(data)
        evidence = None
        if features:
            evidence = _parse_feature(features[0].get("properties", {}), locality, self.source)
        cache[key] = evidence
        if len(cache) > 256:
            cache.popitem(last=False)
        return evidence
