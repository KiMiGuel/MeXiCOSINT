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

# The current IPQS documentation uses the www host for the key-in-path form.
# Keep the key out of query strings and pass the E.164 digits without a plus sign.
_IPQS_URL = "https://www.ipqualityscore.com/api/json/phone"
_SUPPORTED_FIELDS = (
    "valid",
    "active",
    "fraud_score",
    "recent_abuse",
    "VOIP",
    "carrier",
    "line_type",
)


def _payload_detail(data: dict) -> str:
    message = data.get("message")
    if message:
        return str(message)
    errors = data.get("errors")
    if isinstance(errors, list):
        return "; ".join(str(error) for error in errors)
    if errors:
        return str(errors)
    return "IPQualityScore returned an unsuccessful response"


def _raise_api_error(data: dict, http_status: int) -> None:
    """Turn IPQS JSON error envelopes into typed, actionable states.

    IPQS commonly returns HTTP 200 with ``success: false`` for an invalid
    key, exhausted credits, or an invalid phone number.  Treating that as a
    malformed schema hides the actual reason behind ``invalid_response``.
    """
    detail = _payload_detail(data)
    lowered = detail.lower()
    provider_code = str(data.get("request_id") or data.get("error_code") or "")

    if any(
        marker in lowered
        for marker in (
            "invalid api key",
            "invalid access key",
            "unauthorized",
            "forbidden",
            "authentication",
        )
    ):
        state = ProviderState.AUTH_FAILED
    elif any(marker in lowered for marker in ("credit", "quota", "rate limit", "too many requests")):
        state = ProviderState.QUOTA_EXCEEDED
    elif any(marker in lowered for marker in ("invalid/nonexistent phone", "no country specified")):
        state = ProviderState.NO_RESULT
    else:
        state = ProviderState.PROVIDER_ERROR

    raise ProviderRequestError(
        state,
        f"IPQualityScore API error: {detail}",
        http_status=http_status,
        provider_code=provider_code,
    )


def _validate_payload(data) -> dict:
    if not isinstance(data, dict):
        raise ProviderRequestError(
            ProviderState.INVALID_RESPONSE,
            "IPQualityScore returned a non-object JSON response",
            http_status=200,
        )
    if data.get("success") is False:
        _raise_api_error(data, 200)
    if not any(field in data for field in _SUPPORTED_FIELDS):
        raise ProviderRequestError(
            ProviderState.INVALID_RESPONSE,
            "IPQualityScore returned an unsupported response schema",
            http_status=200,
        )
    return data


def _raise_for_status(status_code: int) -> None:
    if status_code in (401, 403):
        state = ProviderState.AUTH_FAILED
    elif status_code == 429:
        state = ProviderState.QUOTA_EXCEEDED
    else:
        state = ProviderState.PROVIDER_ERROR
    raise ProviderRequestError(
        state,
        f"IPQualityScore HTTP {status_code}",
        http_status=status_code,
    )


def _parse_evidence(data, source: str) -> ReputationEvidence:
    data = _validate_payload(data)
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
        return f"{_IPQS_URL}/{self.api_key}/{number.international_digits}"

    def lookup(self, number: NormalizedNumber) -> ReputationEvidence | None:
        if not self.api_key or not number.international_digits:
            return None
        try:
            response = requests.get(
                self._url(number),
                params={"country": "MX", "strictness": 1},
                timeout=self.timeout,
            )
            if response.status_code != 200:
                _raise_for_status(response.status_code)
            return _parse_evidence(
                decode_json_response(response, "IPQualityScore"),
                self.source,
            )
        except ProviderRequestError:
            raise
        except requests.RequestException as exc:
            raise ProviderRequestError(
                ProviderState.PROVIDER_ERROR,
                f"IPQualityScore request failed: {exc}",
            ) from exc

    async def alookup(self, session: aiohttp.ClientSession, number: NormalizedNumber) -> ReputationEvidence | None:
        if not self.api_key or not number.international_digits:
            return None
        try:
            async with session.get(
                self._url(number),
                params={"country": "MX", "strictness": 1},
                timeout=aiohttp.ClientTimeout(total=self.timeout),
            ) as response:
                if response.status != 200:
                    _raise_for_status(response.status)
                try:
                    data = await response.json(content_type=None)
                except (TypeError, ValueError, aiohttp.ContentTypeError) as exc:
                    raise ProviderRequestError(
                        ProviderState.INVALID_RESPONSE,
                        "IPQualityScore returned malformed JSON",
                        http_status=response.status,
                    ) from exc
            return _parse_evidence(data, self.source)
        except ProviderRequestError:
            raise
        except aiohttp.ClientError as exc:
            raise ProviderRequestError(
                ProviderState.PROVIDER_ERROR,
                f"IPQualityScore request failed: {exc}",
            ) from exc
