"""Verificar Emails HLR/MNP phone provider."""

from __future__ import annotations

import aiohttp
import requests

from mexicosint.numbering import NormalizedNumber
from mexicosint.providers.base import Provider
from mexicosint.providers.status import (
    ProviderRequestError,
    ProviderState,
    decode_json_response,
)

_API_URL = "https://dashboard.verificaremails.com/myapi/phone/validate/single"


def _result_payload(data) -> dict:
    if not isinstance(data, dict):
        raise ProviderRequestError(
            ProviderState.INVALID_RESPONSE,
            "Verificar Emails returned a non-object response",
            http_status=200,
        )

    candidate = data
    for _ in range(3):
        nested = candidate.get("result") if isinstance(candidate, dict) else None
        if not isinstance(nested, dict):
            break
        candidate = nested

    if any(
        key in candidate
        for key in ("phone_number", "reachable", "current_network", "original_network")
    ):
        return candidate

    result_code = data.get("result_code") or candidate.get("result_code")
    result_type = data.get("result_type") or candidate.get("result_type")
    message = data.get("message") or candidate.get("message")
    details = []
    if result_code:
        details.append(f"result_code={result_code}")
    if result_type:
        details.append(f"result_type={result_type}")
    if message:
        details.append(f"message={message}")
    suffix = f" ({'; '.join(details)})" if details else ""
    raise ProviderRequestError(
        ProviderState.NO_RESULT,
        f"Verificar Emails returned no HLR/MNP data{suffix}",
        http_status=200,
        provider_code=str(result_code or ""),
    )


def _validate_payload(data) -> dict:
    payload = _result_payload(data)
    if not any(
        field in payload
        for field in ("phone_number", "reachable", "current_network", "original_network")
    ):
        raise ProviderRequestError(
            ProviderState.INVALID_RESPONSE,
            "Verificar Emails returned no HLR/MNP fields",
            http_status=200,
        )
    return payload


def _raise_for_status(status_code: int) -> None:
    if status_code in (401, 403):
        state = ProviderState.AUTH_FAILED
    elif status_code in (402, 429):
        state = ProviderState.QUOTA_EXCEEDED
    else:
        state = ProviderState.PROVIDER_ERROR
    raise ProviderRequestError(
        state,
        f"Verificar Emails HTTP {status_code}",
        http_status=status_code,
    )


class VerificarEmailsProvider(Provider[dict]):
    source = "Verificar Emails"

    def lookup(self, number: NormalizedNumber) -> dict | None:
        if not self.api_key or not number.international_digits:
            return None
        try:
            response = requests.get(
                _API_URL,
                params={
                    "term": number.international_digits,
                    "auth-token": self.api_key,
                },
                timeout=self.timeout,
            )
            if response.status_code != 200:
                _raise_for_status(response.status_code)
            return _validate_payload(decode_json_response(response, self.source))
        except ProviderRequestError:
            raise
        except requests.RequestException as exc:
            raise ProviderRequestError(
                ProviderState.PROVIDER_ERROR,
                f"Verificar Emails request failed: {exc}",
            ) from exc

    async def alookup(
        self,
        session: aiohttp.ClientSession,
        number: NormalizedNumber,
    ) -> dict | None:
        if not self.api_key or not number.international_digits:
            return None
        try:
            async with session.get(
                _API_URL,
                params={
                    "term": number.international_digits,
                    "auth-token": self.api_key,
                },
                timeout=aiohttp.ClientTimeout(total=self.timeout),
            ) as response:
                if response.status != 200:
                    _raise_for_status(response.status)
                try:
                    data = await response.json(content_type=None)
                except (TypeError, ValueError, aiohttp.ContentTypeError) as exc:
                    raise ProviderRequestError(
                        ProviderState.INVALID_RESPONSE,
                        "Verificar Emails returned malformed JSON",
                        http_status=response.status,
                    ) from exc
            return _validate_payload(data)
        except ProviderRequestError:
            raise
        except aiohttp.ClientError as exc:
            raise ProviderRequestError(
                ProviderState.PROVIDER_ERROR,
                f"Verificar Emails request failed: {exc}",
            ) from exc
