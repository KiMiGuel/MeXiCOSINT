from mexicosint.numbering import normalize_mx_number
from mexicosint.providers.geoapify import GeoapifyProvider
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
