"""Google Places public business-listing lookup."""

from __future__ import annotations

import requests

from mexicosint.numbering import NormalizedNumber
from mexicosint.providers.models import BusinessListingEvidence


class GooglePlacesError(Exception):
    def __init__(self, diagnostic: dict):
        self.diagnostic = diagnostic
        super().__init__(
            "Google Places "
            f"{diagnostic.get('failure_kind', 'failure')}: "
            f"HTTP {diagnostic.get('http_status')}; "
            f"Google {diagnostic.get('google_status')}; "
            f"{diagnostic.get('message', '')}"
        )


def _sanitize_message(message: str, api_key: str = "") -> str:
    message = (message or "").replace("\n", " ").replace("\r", " ").strip()
    if api_key:
        message = message.replace(api_key, "[REDACTED]")
    return message[:240]


def _failure_kind(http_status: int | None, google_status: str) -> str:
    google_status = (google_status or "").upper()
    if google_status in {"INVALID_ARGUMENT", "FAILED_PRECONDITION"} or http_status == 400:
        return "malformed request"
    if google_status in {"RESOURCE_EXHAUSTED"} or http_status == 429:
        return "quota failure"
    if google_status in {"PERMISSION_DENIED", "UNAUTHENTICATED", "REQUEST_DENIED"} or http_status in {401, 403}:
        return "billing/auth/config failure"
    return "network failure" if http_status is None else "billing/auth/config failure"


def _parse_google_error(payload: dict) -> tuple[int | None, str, str]:
    error = payload.get("error") if isinstance(payload, dict) else {}
    if not isinstance(error, dict):
        error = {}
    return error.get("code"), error.get("status", ""), error.get("message", "")


def _format_mx_phone_query(number: NormalizedNumber) -> str:
    national = number.national_number or ""
    if len(national) == 10:
        return f"+52 {national[:3]} {national[3:6]} {national[6:]}"
    return number.e164


class GooglePlacesProvider:
    source = "Google Places"
    endpoint_type = "new"

    def __init__(self, api_key: str, timeout: int = 8):
        self.api_key = api_key
        self.timeout = timeout

    def lookup(self, number: NormalizedNumber) -> BusinessListingEvidence | None:
        if not self.api_key or not number.e164:
            return None
        payload = {"textQuery": _format_mx_phone_query(number), "regionCode": "MX"}
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": (
                "places.id,places.displayName,places.formattedAddress,"
                "places.primaryType,places.googleMapsUri,"
                "places.internationalPhoneNumber,places.websiteUri"
            ),
        }
        try:
            response = requests.post(
                "https://places.googleapis.com/v1/places:searchText",
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
        except Exception as exc:
            raise GooglePlacesError(
                {
                    "provider": self.source,
                    "endpoint_type": self.endpoint_type,
                    "failure_kind": "network failure",
                    "http_status": None,
                    "google_status": "",
                    "google_code": None,
                    "message": _sanitize_message(str(exc), self.api_key),
                }
            ) from exc

        try:
            data = response.json()
        except Exception:
            data = {}

        if response.status_code >= 400:
            google_code, google_status, message = _parse_google_error(data)
            raise GooglePlacesError(
                {
                    "provider": self.source,
                    "endpoint_type": self.endpoint_type,
                    "failure_kind": _failure_kind(response.status_code, google_status),
                    "http_status": response.status_code,
                    "google_status": google_status,
                    "google_code": google_code,
                    "message": _sanitize_message(message or response.text, self.api_key),
                }
            )

        places = data.get("places") or []
        if not places:
            return BusinessListingEvidence(
                source=self.source,
                match_status="no_public_listing",
                note="No public business listing found; this is not subscriber identification.",
                raw=data,
            )
        place = places[0]
        return BusinessListingEvidence(
            source=self.source,
            match_status="possible_public_listing",
            name=(place.get("displayName") or {}).get("text", ""),
            category=place.get("primaryType") or "",
            public_address=place.get("formattedAddress") or "",
            website=place.get("websiteUri") or "",
            maps_url=place.get("googleMapsUri") or "",
            place_id=place.get("id") or "",
            note="Possible public business listing only; not subscriber identification.",
            raw=place,
        )
