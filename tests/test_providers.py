from mexicosint.numbering import normalize_mx_number
from mexicosint.providers.geoapify import GeoapifyProvider
from mexicosint.providers.google_places import GooglePlacesProvider
from mexicosint.providers.google_places import GooglePlacesError
from mexicosint.providers.ipqualityscore import IPQualityScoreProvider
from mexicosint.providers.opencage import OpenCageProvider


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code
        self.text = "fake"

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(self.status_code)


def test_geoapify_normalizes_numbering_locality(monkeypatch):
    calls = []

    def fake_get(url, params=None, headers=None, timeout=None):
        calls.append((url, params, timeout))
        return FakeResponse(
            {
                "features": [
                    {
                        "properties": {
                            "city": "Tijuana",
                            "state": "Baja California",
                            "country": "Mexico",
                            "formatted": "Tijuana, Baja California, Mexico",
                            "lat": 32.5149,
                            "lon": -117.0382,
                        }
                    }
                ]
            }
        )

    monkeypatch.setattr("mexicosint.providers.geoapify.requests.get", fake_get)
    provider = GeoapifyProvider("key")

    result = provider.lookup("Tijuana, Baja California, Mexico")

    assert result.source == "Geoapify"
    assert result.kind == "numbering_locality"
    assert result.city == "Tijuana"
    assert result.country_code == "MX"
    assert result.latitude == 32.5149
    assert calls[0][1]["text"] == "Tijuana, Baja California, Mexico"
    assert calls[0][1]["filter"] == "countrycode:mx"
    assert calls[0][2] <= 10


def test_opencage_normalizes_numbering_locality(monkeypatch):
    calls = []

    def fake_get(url, params=None, headers=None, timeout=None):
        calls.append((url, params, timeout))
        return FakeResponse(
            {
                "results": [
                    {
                        "components": {
                            "city": "Tijuana",
                            "state": "Baja California",
                            "country": "Mexico",
                            "country_code": "mx",
                        },
                        "formatted": "Tijuana, Baja California, Mexico",
                        "geometry": {"lat": 32.5149, "lng": -117.0382},
                    }
                ]
            }
        )

    monkeypatch.setattr("mexicosint.providers.opencage.requests.get", fake_get)

    result = OpenCageProvider("key").lookup("Tijuana, Baja California, Mexico")

    assert result.source == "OpenCage"
    assert result.kind == "numbering_locality"
    assert result.city == "Tijuana"
    assert result.state == "Baja California"
    assert result.latitude == 32.5149
    assert result.longitude == -117.0382
    assert calls[0][1]["q"] == "Tijuana, Baja California, Mexico"
    assert calls[0][1]["countrycode"] == "mx"


def test_google_places_normalizes_public_listing(monkeypatch):
    def fake_post(url, json=None, params=None, headers=None, timeout=None):
        return FakeResponse(
            {
                "places": [
                    {
                        "id": "places/abc",
                        "displayName": {"text": "Taller Ejemplo"},
                        "primaryTypeDisplayName": {"text": "Auto repair shop"},
                        "formattedAddress": "Tijuana, Baja California",
                        "websiteUri": "https://example.test",
                        "googleMapsUri": "https://maps.google.com/?cid=1",
                    }
                ]
            }
        )

    monkeypatch.setattr("mexicosint.providers.google_places.requests.post", fake_post)
    number = normalize_mx_number("6634647308")

    result = GooglePlacesProvider("key").lookup(number)

    assert result.source == "Google Places"
    assert result.match_status == "possible_public_listing"
    assert result.name == "Taller Ejemplo"
    assert result.place_id == "places/abc"


def test_google_places_new_text_search_uses_post_json_body(monkeypatch):
    calls = []

    def fake_post(url, json=None, params=None, headers=None, timeout=None):
        calls.append(
            {
                "url": url,
                "json": json,
                "params": params,
                "headers": headers,
                "timeout": timeout,
            }
        )
        return FakeResponse({})

    monkeypatch.setattr("mexicosint.providers.google_places.requests.post", fake_post)

    GooglePlacesProvider("secret-key").lookup(normalize_mx_number("6644837308"))

    assert calls == [
        {
            "url": "https://places.googleapis.com/v1/places:searchText",
            "json": {"textQuery": "+52 664 483 7308", "regionCode": "MX"},
            "params": None,
            "headers": {
                "Content-Type": "application/json",
                "X-Goog-Api-Key": "secret-key",
                "X-Goog-FieldMask": (
                    "places.id,places.displayName,places.formattedAddress,"
                    "places.primaryType,places.googleMapsUri,"
                    "places.internationalPhoneNumber,places.websiteUri"
                ),
            },
            "timeout": 8,
        }
    ]


def test_google_places_reports_successful_zero_results(monkeypatch):
    def fake_post(url, json=None, params=None, headers=None, timeout=None):
        return FakeResponse({})

    monkeypatch.setattr("mexicosint.providers.google_places.requests.post", fake_post)

    result = GooglePlacesProvider("key").lookup(normalize_mx_number("6634647308"))

    assert result.match_status == "no_public_listing"


def test_google_places_sanitizes_http_billing_auth_failure(monkeypatch):
    def fake_post(url, json=None, params=None, headers=None, timeout=None):
        return FakeResponse(
            {
                "error": {
                    "code": 403,
                    "status": "PERMISSION_DENIED",
                    "message": "API key not valid. Please pass a valid API key.",
                }
            },
            status_code=403,
        )

    monkeypatch.setattr("mexicosint.providers.google_places.requests.post", fake_post)

    try:
        GooglePlacesProvider("secret-key").lookup(normalize_mx_number("6634647308"))
    except GooglePlacesError as exc:
        diagnostic = exc.diagnostic
    else:
        raise AssertionError("expected GooglePlacesError")

    assert diagnostic == {
        "provider": "Google Places",
        "endpoint_type": "new",
        "failure_kind": "billing/auth/config failure",
        "http_status": 403,
        "google_status": "PERMISSION_DENIED",
        "google_code": 403,
        "message": "API key not valid. Please pass a valid API key.",
    }
    assert "secret-key" not in str(diagnostic)


def test_google_places_sanitizes_malformed_request(monkeypatch):
    def fake_post(url, json=None, params=None, headers=None, timeout=None):
        return FakeResponse(
            {"error": {"code": 400, "status": "INVALID_ARGUMENT", "message": "Field mask is invalid"}},
            status_code=400,
        )

    monkeypatch.setattr("mexicosint.providers.google_places.requests.post", fake_post)

    try:
        GooglePlacesProvider("secret-key").lookup(normalize_mx_number("6634647308"))
    except GooglePlacesError as exc:
        assert exc.diagnostic["failure_kind"] == "malformed request"
        assert exc.diagnostic["endpoint_type"] == "new"
        assert exc.diagnostic["http_status"] == 400
        assert "secret-key" not in str(exc)
    else:
        raise AssertionError("expected GooglePlacesError")


def test_google_places_sanitizes_quota_failure(monkeypatch):
    def fake_post(url, json=None, params=None, headers=None, timeout=None):
        return FakeResponse(
            {"error": {"code": 429, "status": "RESOURCE_EXHAUSTED", "message": "Quota exceeded"}},
            status_code=429,
        )

    monkeypatch.setattr("mexicosint.providers.google_places.requests.post", fake_post)

    try:
        GooglePlacesProvider("secret-key").lookup(normalize_mx_number("6634647308"))
    except GooglePlacesError as exc:
        assert exc.diagnostic["failure_kind"] == "quota failure"
        assert exc.diagnostic["http_status"] == 429
        assert "secret-key" not in str(exc)
    else:
        raise AssertionError("expected GooglePlacesError")


def test_google_places_sanitizes_network_failure(monkeypatch):
    def fake_post(url, json=None, params=None, headers=None, timeout=None):
        raise RuntimeError("connection refused for secret-key")

    monkeypatch.setattr("mexicosint.providers.google_places.requests.post", fake_post)

    try:
        GooglePlacesProvider("secret-key").lookup(normalize_mx_number("6634647308"))
    except GooglePlacesError as exc:
        assert exc.diagnostic["failure_kind"] == "network failure"
        assert exc.diagnostic["http_status"] is None
        assert "secret-key" not in str(exc)
        assert "secret-key" not in str(exc.diagnostic)
    else:
        raise AssertionError("expected GooglePlacesError")


def test_ipqualityscore_normalizes_phone_evidence(monkeypatch):
    def fake_get(url, params=None, headers=None, timeout=None):
        return FakeResponse(
            {
                "success": True,
                "valid": True,
                "active": True,
                "fraud_score": 12,
                "recent_abuse": False,
                "VOIP": False,
                "carrier": "Telcel",
                "line_type": "Wireless",
                "country": "MX",
                "city": "Tijuana",
                "region": "Baja California",
            }
        )

    monkeypatch.setattr("mexicosint.providers.ipqualityscore.requests.get", fake_get)

    result = IPQualityScoreProvider("key").lookup(normalize_mx_number("6634647308"))

    assert result.source == "IPQualityScore"
    assert result.valid is True
    assert result.active is True
    assert result.risk_score == 12
    assert result.abuse_recent is False
    assert result.carrier == "Telcel"
