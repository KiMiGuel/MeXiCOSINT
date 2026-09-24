"""Abstract Phone Intelligence provider and response parser."""

from __future__ import annotations

import aiohttp
import requests

from mexicosint.providers.base import Provider
from mexicosint.providers.status import (
    ProviderRequestError,
    ProviderState,
    decode_json_response,
)

_URL = "https://phoneintelligence.abstractapi.com/v1/"

SAMPLE_ABSTRACT_INTEL = {
    "phone_number": "+525512345678",
    "phone_format": {
        "international": "+52 55 1234 5678",
        "national": "(55) 1234-5678",
    },
    "phone_carrier": {
        "name": "Telcel",
        "line_type": "mobile",
        "mcc": 334,
        "mnc": 20,
    },
    "phone_location": {
        "country_name": "Mexico",
        "country_code": "MX",
        "country_prefix": "+52",
        "region": "Ciudad de Mexico",
        "city": "Ciudad de Mexico",
        "timezone": "America/Mexico_City",
    },
    "phone_validation": {
        "is_valid": True,
        "line_status": "active",
        "is_voip": False,
    },
    "phone_risk": {
        "risk_level": "low",
        "is_disposable": False,
        "is_abuse_detected": False,
    },
}


class AbstractPhoneIntelligenceProvider(Provider[dict]):
    source = "AbstractAPI"

    def __init__(
        self,
        api_key: str,
        timeout: int = 15,
        session: requests.Session | None = None,
    ):
        super().__init__(api_key, timeout)
        self._session = session

    def _get(self, url: str, **kwargs):
        if self._session is not None:
            return self._session.get(url, **kwargs)
        return requests.get(url, **kwargs)

    def lookup(self, e164: str) -> dict:
        if not self.api_key or not e164:
            raise ValueError("Abstract Phone Intelligence requires a key and phone number")
        try:
            response = self._get(
                _URL,
                params={"api_key": self.api_key, "phone": e164},
                timeout=self.timeout,
            )
            if response.status_code == 200:
                data = decode_json_response(response, "Abstract Phone Intelligence")
                if any(field in data for field in ("phone_number", "phone", "format")):
                    return data
        except requests.RequestException as exc:
            response = getattr(exc, "response", None)
            status = getattr(response, "status_code", None)
            text = getattr(response, "text", "N/A")[:200]
            if status in (401, 403):
                state = ProviderState.AUTH_FAILED
            elif status == 429:
                state = ProviderState.QUOTA_EXCEEDED
            else:
                state = ProviderState.PROVIDER_ERROR
            raise ProviderRequestError(
                state,
                f"Abstract Phone Intelligence API: HTTP {status} - {text}",
                http_status=status,
            ) from exc
        if 200 <= response.status_code < 300:
            state = ProviderState.INVALID_RESPONSE
        elif response.status_code in (401, 403):
            state = ProviderState.AUTH_FAILED
        elif response.status_code == 429:
            state = ProviderState.QUOTA_EXCEEDED
        else:
            state = ProviderState.PROVIDER_ERROR
        raise ProviderRequestError(
            state,
            f"Abstract Phone Intelligence API: HTTP {response.status_code}",
            http_status=response.status_code,
        )

    async def alookup(
        self, session: aiohttp.ClientSession, e164: str
    ) -> dict:
        if not self.api_key or not e164:
            raise ValueError("Abstract Phone Intelligence requires a key and phone number")
        try:
            async with session.get(
                _URL,
                params={"api_key": self.api_key, "phone": e164},
                timeout=aiohttp.ClientTimeout(total=self.timeout),
            ) as response:
                if response.status == 200:
                    try:
                        data = await response.json(content_type=None)
                    except (TypeError, ValueError, aiohttp.ContentTypeError) as exc:
                        raise ProviderRequestError(
                            ProviderState.INVALID_RESPONSE,
                            "Abstract Phone Intelligence returned malformed JSON",
                            http_status=response.status,
                        ) from exc
                    if any(
                        field in data
                        for field in ("phone_number", "phone", "format")
                    ):
                        return data
                if 200 <= response.status < 300:
                    state = ProviderState.INVALID_RESPONSE
                elif response.status in (401, 403):
                    state = ProviderState.AUTH_FAILED
                elif response.status == 429:
                    state = ProviderState.QUOTA_EXCEEDED
                else:
                    state = ProviderState.PROVIDER_ERROR
                raise ProviderRequestError(
                    state,
                    f"Abstract Phone Intelligence API: HTTP {response.status}",
                    http_status=response.status,
                )
        except aiohttp.ClientError as exc:
            raise ProviderRequestError(
                ProviderState.PROVIDER_ERROR,
                f"Abstract Phone Intelligence API: {exc}",
            ) from exc


def parse_abstract(data: dict) -> dict:
    """Normalize the supported Abstract response schemas."""
    if "phone_number" in data:
        phone_validation = data.get("phone_validation", {})
        phone_format = data.get("phone_format", {})
        phone_location = data.get("phone_location", {})
        phone_carrier = data.get("phone_carrier", {})
        phone_risk = data.get("phone_risk", {})
        return {
            "product": "Phone Intelligence",
            "valid": phone_validation.get("is_valid"),
            "international": phone_format.get("international"),
            "national": phone_format.get("national"),
            "country": phone_location.get("country_name"),
            "location": phone_location.get("city")
            or phone_location.get("region"),
            "carrier": phone_carrier.get("name"),
            "line_type": phone_carrier.get("line_type"),
            "risk_level": phone_risk.get("risk_level"),
            "raw": data,
        }

    valid = data.get("valid", data.get("is_valid"))
    if "phone" in data:
        return {
            "product": "Phone Validation",
            "valid": valid,
            "phone": data.get("phone"),
            "country": data.get("country_name", data.get("country")),
            "location": data.get("location"),
            "carrier": data.get("carrier"),
            "line_type": data.get("type"),
            "risk_level": None,
            "raw": data,
        }

    if "format" in data:
        fmt = data.get("format", {})
        country = data.get("country", {})
        return {
            "product": "Phone Validation",
            "valid": valid,
            "international": fmt.get("international"),
            "national": fmt.get("local", fmt.get("national")),
            "country": country.get("name"),
            "location": data.get("location"),
            "carrier": data.get("carrier"),
            "line_type": data.get("type"),
            "risk_level": None,
            "raw": data,
        }

    return {"product": "Desconocido", "raw": data}
