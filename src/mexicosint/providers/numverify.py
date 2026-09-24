"""NumVerify phone-validation provider and response parser."""

from __future__ import annotations

import aiohttp
import requests

from mexicosint.providers.base import Provider
from mexicosint.providers.status import (
    ProviderRequestError,
    ProviderState,
    decode_json_response,
)

_LEGACY_URL = "https://apilayer.net/api/validate"
_MARKETPLACE_URL = "https://api.apilayer.com/number_verification/validate"

SAMPLE_NUMVERIFY = {
    "valid": True,
    "local_format": "5512345678",
    "international_format": "+525512345678",
    "country_name": "Mexico",
    "country_code": "MX",
    "location": "Mexico City",
    "carrier": "Telcel",
    "line_type": "mobile",
}


class NumVerifyProvider(Provider[dict]):
    source = "NumVerify"

    def __init__(
        self,
        api_key: str,
        timeout: int = 15,
        session: requests.Session | None = None,
    ):
        super().__init__(api_key, timeout)
        self._session = session

    def _legacy_params(self, e164: str) -> dict:
        return {
            "access_key": self.api_key,
            "number": e164.replace("+", ""),
            "format": 1,
        }

    @staticmethod
    def _marketplace_params(e164: str) -> dict:
        return {"number": e164.replace("+", "")}

    def _marketplace_headers(self) -> dict:
        return {"apikey": self.api_key}

    @staticmethod
    def _validate_payload(data: dict) -> dict:
        if data.get("error"):
            err_info = data.get("error", {})
            info = str(err_info.get("info", "Unknown"))
            code = str(err_info.get("code", ""))
            provider_id = str(err_info.get("id", ""))
            lowered = info.lower()
            if any(
                marker in lowered
                for marker in ("api key", "access key", "authentication", "unauthorized")
            ):
                state = ProviderState.AUTH_FAILED
            elif any(marker in lowered for marker in ("quota", "limit", "monthly")):
                state = ProviderState.QUOTA_EXCEEDED
            else:
                state = ProviderState.PROVIDER_ERROR
            raise ProviderRequestError(
                state,
                f"Numverify API Error: {info}",
                provider_code=code or provider_id,
            )
        if not any(
            field in data
            for field in (
                "valid",
                "number",
                "local_format",
                "international_format",
                "country_code",
            )
        ):
            raise ProviderRequestError(
                ProviderState.INVALID_RESPONSE,
                "Numverify returned an unsupported response schema",
                http_status=200,
            )
        return data

    def _get(self, url: str, **kwargs):
        if self._session is not None:
            return self._session.get(url, **kwargs)
        return requests.get(url, **kwargs)

    @staticmethod
    def _raise_for_status(status_code: int) -> None:
        if status_code in (401, 403):
            state = ProviderState.AUTH_FAILED
        elif status_code == 429:
            state = ProviderState.QUOTA_EXCEEDED
        else:
            state = ProviderState.PROVIDER_ERROR
        raise ProviderRequestError(
            state,
            f"Numverify HTTP {status_code}",
            http_status=status_code,
        )

    def _decode_response(self, response) -> dict:
        if response.status_code != 200:
            self._raise_for_status(response.status_code)
        return self._validate_payload(
            decode_json_response(response, "NumVerify")
        )

    def _should_fallback(self, error: ProviderRequestError) -> bool:
        return error.state != ProviderState.QUOTA_EXCEEDED

    def lookup(self, e164: str) -> dict:
        if not self.api_key or not e164:
            raise ValueError("NumVerify requires a key and phone number")
        legacy_error: ProviderRequestError | None = None
        try:
            response = self._get(
                _LEGACY_URL,
                params=self._legacy_params(e164),
                timeout=self.timeout,
            )
            return self._decode_response(response)
        except ProviderRequestError as exc:
            legacy_error = exc
            if not self._should_fallback(legacy_error):
                raise
        except requests.RequestException as exc:
            legacy_error = ProviderRequestError(
                ProviderState.PROVIDER_ERROR,
                f"Numverify legacy endpoint: {exc}",
            )

        try:
            response = self._get(
                _MARKETPLACE_URL,
                params=self._marketplace_params(e164),
                headers=self._marketplace_headers(),
                timeout=self.timeout,
            )
            return self._decode_response(response)
        except (ProviderRequestError, requests.RequestException) as marketplace_error:
            if isinstance(marketplace_error, requests.RequestException):
                marketplace_error = ProviderRequestError(
                    ProviderState.PROVIDER_ERROR,
                    f"Numverify marketplace endpoint: {marketplace_error}",
                )
            raise marketplace_error from legacy_error

    async def _alookup_endpoint(
        self,
        session: aiohttp.ClientSession,
        url: str,
        params: dict,
        headers: dict | None = None,
    ) -> dict:
        try:
            async with session.get(
                url,
                params=params,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=self.timeout),
            ) as response:
                if response.status != 200:
                    self._raise_for_status(response.status)
                try:
                    data = await response.json(content_type=None)
                except (TypeError, ValueError, aiohttp.ContentTypeError) as exc:
                    raise ProviderRequestError(
                        ProviderState.INVALID_RESPONSE,
                        "NumVerify returned malformed JSON",
                        http_status=response.status,
                    ) from exc
        except aiohttp.ClientError as exc:
            raise ProviderRequestError(
                ProviderState.PROVIDER_ERROR,
                f"Numverify endpoint: {exc}",
            ) from exc
        return self._validate_payload(data)

    async def alookup(self, session: aiohttp.ClientSession, e164: str) -> dict:
        if not self.api_key or not e164:
            raise ValueError("NumVerify requires a key and phone number")
        legacy_error: ProviderRequestError | None = None
        try:
            return await self._alookup_endpoint(
                session,
                _LEGACY_URL,
                self._legacy_params(e164),
            )
        except ProviderRequestError as exc:
            legacy_error = exc
            if not self._should_fallback(legacy_error):
                raise
        try:
            return await self._alookup_endpoint(
                session,
                _MARKETPLACE_URL,
                self._marketplace_params(e164),
                self._marketplace_headers(),
            )
        except ProviderRequestError as marketplace_error:
            raise marketplace_error from legacy_error


def parse_numverify(data: dict) -> dict:
    return {
        "valid": data.get("valid"),
        "local_format": data.get("local_format"),
        "international_format": data.get("international_format"),
        "country": data.get("country_name"),
        "location": data.get("location"),
        "carrier": data.get("carrier"),
        "line_type": data.get("line_type"),
        "raw": data,
    }
