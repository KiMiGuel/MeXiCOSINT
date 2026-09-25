import pytest

from mexicosint.numbering import normalize_mx_number
from mexicosint.providers.abstract import (
    AbstractPhoneIntelligenceProvider,
    parse_abstract,
)
from mexicosint.providers.geoapify import GeoapifyProvider
from mexicosint.providers.ipqualityscore import IPQualityScoreProvider
from mexicosint.providers.numverify import NumVerifyProvider, parse_numverify
from mexicosint.providers.nominatim import NominatimProvider
from mexicosint.providers.opencage import OpenCageProvider
from mexicosint.providers.status import ProviderRequestError, ProviderState


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


def test_nominatim_fallback_normalizes_mexican_locality(monkeypatch):
    calls = []

    def fake_get(url, params=None, headers=None, timeout=None):
        calls.append((url, params, headers, timeout))
        return FakeResponse(
            [
                {
                    "lat": "32.5149",
                    "lon": "-117.0382",
                    "display_name": "Tijuana, Baja California, Mexico",
                }
            ]
        )

    monkeypatch.setattr(
        "mexicosint.providers.nominatim.requests.get",
        fake_get,
    )
    result = NominatimProvider(timeout=6).lookup(
        "Tijuana, Baja California, Mexico"
    )

    assert result.source == "Nominatim"
    assert result.country_code == "MX"
    assert result.latitude == 32.5149
    assert result.longitude == -117.0382
    assert calls[0][1]["q"] == "Tijuana, Baja California, Mexico"
    assert calls[0][1]["countrycodes"] == "mx"
    assert "MeXiCOSINT/" in calls[0][2]["User-Agent"]
    assert calls[0][3] == 6


def test_geoapify_result_without_coordinates_is_invalid_response(monkeypatch):
    monkeypatch.setattr(
        "mexicosint.providers.geoapify.requests.get",
        lambda *args, **kwargs: FakeResponse(
            {"features": [{"properties": {"city": "Tijuana"}}]}
        ),
    )

    with pytest.raises(ProviderRequestError) as exc_info:
        GeoapifyProvider("key").lookup("Tijuana")

    assert exc_info.value.state == ProviderState.INVALID_RESPONSE


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


def test_ipqualityscore_api_error_envelope_is_classified(monkeypatch):
    monkeypatch.setattr(
        "mexicosint.providers.ipqualityscore.requests.get",
        lambda *args, **kwargs: FakeResponse(
            {
                "success": False,
                "message": "Invalid API key.",
                "request_id": "request-123",
            }
        ),
    )

    with pytest.raises(ProviderRequestError) as exc_info:
        IPQualityScoreProvider("bad-key").lookup(normalize_mx_number("6634647308"))

    assert exc_info.value.state == ProviderState.AUTH_FAILED
    assert exc_info.value.http_status == 200
    assert exc_info.value.provider_code == "request-123"
    assert "Invalid API key" in exc_info.value.detail


def test_ipqualityscore_invalid_phone_is_no_result(monkeypatch):
    monkeypatch.setattr(
        "mexicosint.providers.ipqualityscore.requests.get",
        lambda *args, **kwargs: FakeResponse(
            {
                "success": False,
                "message": "Invalid/nonexistent phone number or no country specified.",
            }
        ),
    )

    with pytest.raises(ProviderRequestError) as exc_info:
        IPQualityScoreProvider("key").lookup(normalize_mx_number("6634647308"))

    assert exc_info.value.state == ProviderState.NO_RESULT


def test_ipqualityscore_uses_documented_www_endpoint():
    provider = IPQualityScoreProvider("key")
    assert provider._url(normalize_mx_number("6634647308")).startswith(
        "https://www.ipqualityscore.com/api/json/phone/key/"
    )


def test_abstract_provider_builds_request_and_parses_phone_intelligence(monkeypatch):
    calls = []

    def fake_get(url, params=None, headers=None, timeout=None):
        calls.append((url, params, timeout))
        return FakeResponse(
            {
                "phone_number": "+525512345678",
                "phone_validation": {
                    "is_valid": True,
                    "line_status": "active",
                    "is_voip": False,
                },
                "phone_format": {
                    "international": "+52 55 1234 5678",
                    "national": "55 1234 5678",
                },
                "phone_location": {"country_name": "Mexico", "city": "CDMX"},
                "phone_carrier": {"name": "Telcel", "line_type": "mobile"},
                "phone_risk": {
                    "risk_level": "low",
                    "is_disposable": False,
                    "is_abuse_detected": False,
                },
            }
        )

    monkeypatch.setattr("mexicosint.providers.abstract.requests.get", fake_get)
    raw = AbstractPhoneIntelligenceProvider("key", timeout=9).lookup(
        "+525512345678"
    )
    parsed = parse_abstract(raw)

    assert calls[0][1] == {
        "api_key": "key",
        "phone": "+525512345678",
    }
    assert calls[0][2] == 9
    assert parsed["product"] == "Phone Intelligence"
    assert parsed["valid"] is True
    assert parsed["location"] == "CDMX"
    assert parsed["carrier"] == "Telcel"
    assert parsed["line_status"] == "active"
    assert parsed["is_voip"] is False
    assert parsed["is_disposable"] is False
    assert parsed["abuse_detected"] is False


def test_numverify_provider_builds_request_and_normalizes(monkeypatch):
    calls = []

    def fake_get(url, params=None, headers=None, timeout=None):
        calls.append((url, params, timeout))
        return FakeResponse(
            {
                "valid": True,
                "local_format": "5512345678",
                "international_format": "+525512345678",
                "country_name": "Mexico",
                "location": "Ciudad de Mexico",
                "carrier": "Telcel",
                "line_type": "mobile",
            }
        )

    monkeypatch.setattr("mexicosint.providers.numverify.requests.get", fake_get)
    raw = NumVerifyProvider("key", timeout=7).lookup("+525512345678")
    parsed = parse_numverify(raw)

    assert calls[0][1] == {
        "access_key": "key",
        "number": "525512345678",
        "format": 1,
    }
    assert calls[0][2] == 7
    assert parsed["valid"] is True
    assert parsed["country"] == "Mexico"
    assert parsed["location"] == "Ciudad de Mexico"


def test_abstract_unsupported_success_payload_is_invalid_response(monkeypatch):
    monkeypatch.setattr(
        "mexicosint.providers.abstract.requests.get",
        lambda *args, **kwargs: FakeResponse({"unexpected": True}),
    )

    with pytest.raises(ProviderRequestError) as exc_info:
        AbstractPhoneIntelligenceProvider("key").lookup("+525512345678")

    assert exc_info.value.state == ProviderState.INVALID_RESPONSE
    assert exc_info.value.http_status == 200


def test_abstract_malformed_json_is_invalid_response(monkeypatch):
    class MalformedResponse(FakeResponse):
        def json(self):
            raise ValueError("malformed json")

    monkeypatch.setattr(
        "mexicosint.providers.abstract.requests.get",
        lambda *args, **kwargs: MalformedResponse({}),
    )

    with pytest.raises(ProviderRequestError) as exc_info:
        AbstractPhoneIntelligenceProvider("key").lookup("+525512345678")

    assert exc_info.value.state == ProviderState.INVALID_RESPONSE
    assert exc_info.value.http_status == 200


def test_numverify_http_auth_failure_is_typed(monkeypatch):
    response = FakeResponse({}, status_code=401)
    monkeypatch.setattr(
        "mexicosint.providers.numverify.requests.get",
        lambda *args, **kwargs: response,
    )

    with pytest.raises(ProviderRequestError) as exc_info:
        NumVerifyProvider("key").lookup("+525512345678")

    assert exc_info.value.state == ProviderState.AUTH_FAILED
    assert exc_info.value.http_status == 401


def test_numverify_falls_back_to_marketplace_endpoint(monkeypatch):
    calls = []

    def fake_get(url, params=None, headers=None, timeout=None):
        calls.append((url, params, headers))
        if len(calls) == 1:
            return FakeResponse({}, status_code=401)
        return FakeResponse(
            {
                "valid": True,
                "number": "525512345678",
                "country_code": "MX",
                "location": "Ciudad de Mexico",
            }
        )

    monkeypatch.setattr(
        "mexicosint.providers.numverify.requests.get",
        fake_get,
    )
    result = NumVerifyProvider("market-key").lookup("+525512345678")

    assert result["valid"] is True
    assert calls[1][0] == "https://api.apilayer.com/number_verification/validate"
    assert calls[1][2] == {"apikey": "market-key"}
    assert calls[1][1] == {"number": "525512345678"}
