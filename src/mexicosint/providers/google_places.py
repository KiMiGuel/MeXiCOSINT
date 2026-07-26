"""Google Places public business-listing lookup."""

from __future__ import annotations

import requests

from mexicosint.numbering import NormalizedNumber
from mexicosint.providers.models import BusinessListingEvidence


class GooglePlacesProvider:
    source = "Google Places"

    def __init__(self, api_key: str, timeout: int = 8):
        self.api_key = api_key
        self.timeout = timeout

    def lookup(self, number: NormalizedNumber) -> BusinessListingEvidence | None:
        if not self.api_key or not number.e164:
            return None
        params = {"textQuery": number.e164, "regionCode": "MX", "languageCode": "es"}
        headers = {
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": (
                "places.id,places.displayName,places.primaryTypeDisplayName,"
                "places.formattedAddress,places.websiteUri,places.googleMapsUri"
            ),
        }
        response = requests.get(
            "https://places.googleapis.com/v1/places:searchText",
            params=params,
            headers=headers,
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = response.json()
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
            category=(place.get("primaryTypeDisplayName") or {}).get("text", ""),
            public_address=place.get("formattedAddress") or "",
            website=place.get("websiteUri") or "",
            maps_url=place.get("googleMapsUri") or "",
            place_id=place.get("id") or "",
            note="Possible public business listing only; not subscriber identification.",
            raw=place,
        )
