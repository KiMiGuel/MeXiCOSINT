"""Nominatim fallback geocoder for Mexican numbering localities."""

from __future__ import annotations

import aiohttp
import requests

from mexicosint import __version__
from mexicosint.core.settings import ScanSettings
from mexicosint.locality import is_concrete_locality
from mexicosint.providers.base import Provider
from mexicosint.providers.models import LocalityEvidence
from mexicosint.providers.status import (
    ProviderRequestError,
    ProviderState,
    decode_json_response,
)

_URL = "https://nominatim.openstreetmap.org/search"
_HEADERS = {"User-Agent": f"MeXiCOSINT/{__version__} (OSINT research)"}
_ASYNC_CACHE: dict[str, LocalityEvidence | None] = {}


def _params(city_region: str) -> dict:
    query = city_region
    if not query.lower().rstrip().endswith(", mexico"):
        query = f"{query}, Mexico"
    return {
        "q": query,
        "format": "json",
        "limit": 1,
        "countrycodes": "mx",
    }


def _parse_result(data: list, locality: str) -> LocalityEvidence | None:
    if not isinstance(data, list):
        raise ProviderRequestError(
            ProviderState.INVALID_RESPONSE,
            "Nominatim returned an unsupported response schema",
            http_status=200,
        )
    if not data:
        return None
    item = data[0]
    return LocalityEvidence(
        source="Nominatim",
        kind="numbering_locality",
        query=locality,
        city="",
        state="",
        country="Mexico",
        country_code="MX",
        formatted_address=item.get("display_name", ""),
        latitude=float(item["lat"]),
        longitude=float(item["lon"]),
        note="Numbering locality only; not live phone or subscriber location.",
        raw=item,
    )


class NominatimProvider(Provider[LocalityEvidence]):
    source = "Nominatim"

    def __init__(
        self,
        api_key: str = "",
        timeout: int = 10,
        session: requests.Session | None = None,
    ):
        super().__init__(api_key, timeout)
        self._session = session

    def _get(self, url: str, **kwargs):
        if self._session is not None:
            return self._session.get(url, **kwargs)
        return requests.get(url, **kwargs)

    def lookup(self, locality: str) -> LocalityEvidence | None:
        if not is_concrete_locality(locality):
            return None
        response = self._get(
            _URL,
            params=_params(locality),
            headers=_HEADERS,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return _parse_result(
            decode_json_response(response, "Nominatim"),
            locality,
        )

    async def alookup(
        self, session: aiohttp.ClientSession, locality: str
    ) -> LocalityEvidence | None:
        if not is_concrete_locality(locality):
            return None
        if locality in _ASYNC_CACHE:
            return _ASYNC_CACHE[locality]
        async with session.get(
            _URL,
            params=_params(locality),
            headers=_HEADERS,
            timeout=aiohttp.ClientTimeout(total=self.timeout),
        ) as response:
            response.raise_for_status()
            try:
                data = await response.json(content_type=None)
            except (TypeError, ValueError, aiohttp.ContentTypeError) as exc:
                raise ProviderRequestError(
                    ProviderState.INVALID_RESPONSE,
                    "Nominatim returned malformed JSON",
                    http_status=response.status,
                ) from exc
        evidence = _parse_result(data, locality)
        _ASYNC_CACHE[locality] = evidence
        return evidence


def _nominatim_sync_cached(
    city_region: str, settings: ScanSettings
) -> tuple[float | None, float | None, str]:
    if city_region in settings.nominatim_cache:
        evidence = settings.nominatim_cache[city_region]
    else:
        evidence = NominatimProvider(
            timeout=settings.default_timeout,
            session=settings.session,
        ).lookup(city_region)
        settings.nominatim_cache[city_region] = evidence
    if evidence is None:
        return None, None, ""
    return evidence.latitude, evidence.longitude, evidence.formatted_address


def geocode_nominatim(
    city_region: str, settings: ScanSettings | None = None
) -> tuple[float | None, float | None, str]:
    settings = settings or ScanSettings()
    if settings.dummy_mode:
        return None, None, ""
    return _nominatim_sync_cached(city_region, settings)


async def _nominatim_async(
    session: aiohttp.ClientSession, city_region: str
) -> tuple[float | None, float | None, str]:
    evidence = await NominatimProvider().alookup(session, city_region)
    if evidence is None:
        return None, None, ""
    return evidence.latitude, evidence.longitude, evidence.formatted_address


geocode_nominatim.async_impl = _nominatim_async
