"""Serializable provider credential and request states."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ProviderState(str, Enum):
    MISSING = "missing"
    NOT_REQUESTED = "not_requested"
    CONFIGURED_UNVERIFIED = "configured_unverified"
    REQUEST_SUCCESS = "request_success"
    NO_RESULT = "no_result"
    PROVIDER_ERROR = "provider_error"
    INVALID_RESPONSE = "invalid_response"
    AUTH_FAILED = "auth_failed"
    QUOTA_EXCEEDED = "quota_exceeded"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class ProviderStatus:
    state: ProviderState
    source: str = ""
    transport: str = "not_requested"
    request_attempted: bool = False
    http_status: int | None = None
    provider_code: str = ""
    detail: str = ""


def decode_json_response(response, provider_name: str):
    """Decode a successful HTTP JSON response with typed invalid-response errors."""
    try:
        return response.json()
    except (TypeError, ValueError) as exc:
        raise ProviderRequestError(
            ProviderState.INVALID_RESPONSE,
            f"{provider_name} returned malformed JSON",
            http_status=getattr(response, "status_code", 200),
        ) from exc


class ProviderRequestError(Exception):
    """Provider failure with classification and non-secret metadata."""

    def __init__(
        self,
        state: ProviderState,
        detail: str,
        *,
        http_status: int | None = None,
        provider_code: str = "",
    ):
        super().__init__(detail)
        self.state = state
        self.detail = detail
        self.http_status = http_status
        self.provider_code = provider_code


def classify_provider_exception(exc: Exception) -> ProviderStatus:
    """Normalize sync/async provider exceptions without exposing credentials."""
    if isinstance(exc, ProviderRequestError):
        return ProviderStatus(
            state=exc.state,
            transport="live_request",
            request_attempted=True,
            http_status=exc.http_status,
            provider_code=exc.provider_code,
            detail=exc.detail,
        )

    response = getattr(exc, "response", None)
    status_code = getattr(response, "status_code", None)
    if status_code is None:
        status_code = getattr(exc, "status", None)
    detail = str(exc) or type(exc).__name__
    lowered = detail.lower()

    if status_code in (401, 403) or any(
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
    elif status_code == 429 or any(
        marker in lowered
        for marker in ("quota", "rate limit", "too many requests", "plan limit")
    ):
        state = ProviderState.QUOTA_EXCEEDED
    elif status_code is not None and 200 <= int(status_code) < 300:
        state = ProviderState.INVALID_RESPONSE
    else:
        state = ProviderState.PROVIDER_ERROR

    return ProviderStatus(
        state=state,
        transport="live_request",
        request_attempted=True,
        http_status=int(status_code) if status_code is not None else None,
        detail=detail,
    )


def with_transport(status: ProviderStatus, transport: str) -> ProviderStatus:
    return ProviderStatus(
        state=status.state,
        source=status.source,
        transport=transport,
        request_attempted=status.request_attempted,
        http_status=status.http_status,
        provider_code=status.provider_code,
        detail=status.detail,
    )
