import json

import mexicosint.main as app


def test_dummy_scan_writes_evidence_state_to_report(monkeypatch, tmp_path):
    monkeypatch.setattr(app, "DUMMY_MODE", True)
    monkeypatch.setattr(app, "REPORT_DIR", tmp_path)
    monkeypatch.setattr(app, "MAP_DIR", tmp_path)

    result = app.run_phone_scan("5512345678", app.init_config(), list(app.SAMPLE_CONFIG))

    report = json.loads((tmp_path / app.Path(result.report_path).name).read_text(encoding="utf-8"))
    assert result.evidence_state == "strong agreement"
    assert report["evidence_state"] == "strong agreement"
    assert report["geoapify_data"]["source"] == "Geoapify"
    assert report["ipqualityscore_data"]["source"] == "IPQualityScore"


def test_dummy_scan_handles_missing_locality_without_geocoding(monkeypatch, tmp_path):
    monkeypatch.setattr(app, "DUMMY_MODE", True)
    monkeypatch.setattr(app, "REPORT_DIR", tmp_path)
    monkeypatch.setattr(app, "MAP_DIR", tmp_path)
    monkeypatch.setattr(app, "IFT_BLOCKS_AVAILABLE", False)
    monkeypatch.setattr(app, "parse_mx_number", lambda raw: {"city": "Unknown", "state": "Unknown", "is_mobile": False, "number_type": "Unknown"})
    monkeypatch.setattr(app, "detect_lada_region", lambda number: "")
    monkeypatch.setattr(app, "geocode_phonenumbers", lambda parsed: "")
    monkeypatch.setattr(app, "parse_abstract", lambda data: {"location": "", "carrier": "", "line_type": ""})
    monkeypatch.setattr(app, "parse_numverify", lambda data: {"location": "", "carrier": "", "line_type": ""})

    result = app.run_phone_scan(
        "5512345678",
        app.init_config(),
        ["abstract_phone_intelligence", "numverify", "opencage", "geoapify"],
    )

    assert result.evidence_state == "no usable locality"
    assert result.geoapify_data == {}
    assert result.report_path


def test_dummy_scan_records_provider_errors(monkeypatch, tmp_path):
    monkeypatch.setattr(app, "DUMMY_MODE", False)
    monkeypatch.setattr(app, "REPORT_DIR", tmp_path)
    monkeypatch.setattr(app, "MAP_DIR", tmp_path)
    monkeypatch.setattr(app, "geocode_nominatim", lambda city: (None, None, ""))
    monkeypatch.setattr(app, "abstract_phone_intelligence_lookup", lambda e164, api_key: (_ for _ in ()).throw(RuntimeError("abstract down")))
    monkeypatch.setattr(app, "numverify_lookup", lambda e164, api_key: (_ for _ in ()).throw(RuntimeError("numverify down")))

    result = app.run_phone_scan(
        "5512345678",
        {
            "abstract_phone_intelligence": "dummy_key_abstract",
            "numverify": "dummy_key_numverify",
        },
        ["abstract_phone_intelligence", "numverify"],
    )

    assert "strong agreement" == result.evidence_state
    assert any("abstract_intel: abstract down" == error for error in result.errors)
    assert any("numverify: numverify down" == error for error in result.errors)


def test_live_scans_use_current_normalized_number_for_phone_providers(monkeypatch, tmp_path):
    calls = {"abstract": [], "numverify": [], "ipqualityscore": []}

    class FakeIpqsProvider:
        def __init__(self, api_key):
            pass

        def lookup(self, number):
            calls["ipqualityscore"].append(number.international_digits)
            return None

    monkeypatch.setattr(app, "DUMMY_MODE", False)
    monkeypatch.setattr(app, "REPORT_DIR", tmp_path)
    monkeypatch.setattr(app, "MAP_DIR", tmp_path)
    monkeypatch.setattr(app, "geocode_nominatim", lambda city: (None, None, ""))
    monkeypatch.setattr(app, "abstract_phone_intelligence_lookup", lambda e164, api_key: calls["abstract"].append(e164) or {})
    monkeypatch.setattr(app, "numverify_lookup", lambda e164, api_key: calls["numverify"].append(e164) or {})
    monkeypatch.setattr(app, "IPQualityScoreProvider", FakeIpqsProvider)

    config = {
        "abstract_phone_intelligence": "present_abs",
        "numverify": "present_num",
        "ipqualityscore": "present_ipq",
    }
    active = list(config)

    first = app.run_phone_scan("5512345678", config, active)
    second = app.run_phone_scan("6634647308", config, active)

    assert calls["abstract"] == ["+525512345678", "+526634647308"]
    assert calls["numverify"] == ["+525512345678", "+526634647308"]
    assert calls["ipqualityscore"] == ["525512345678", "526634647308"]
    assert first.scan_id != second.scan_id
    assert first.provider_trace != second.provider_trace


def test_main_resets_dummy_mode_between_invocations(monkeypatch):
    states = []

    monkeypatch.setattr(app, "print_banner", lambda: None)
    monkeypatch.setattr(app, "init_config", lambda: {})
    monkeypatch.setattr(app, "check_keys", lambda config: [])
    monkeypatch.setattr(app, "print_results", lambda result: None)

    def fake_scan(raw, config, active):
        states.append(app.DUMMY_MODE)
        return app.ScanResult(e164="+525512345678")

    monkeypatch.setattr(app, "run_phone_scan", fake_scan)

    app.main(["--dummy-test", "5512345678"])
    app.main(["5512345678"])

    assert states == [True, False]


def test_vague_locality_is_not_sent_to_geoapify(monkeypatch, tmp_path):
    geo_calls = []

    class FakeGeoapifyProvider:
        def __init__(self, api_key):
            pass

        def lookup(self, locality):
            geo_calls.append(locality)
            return None

    monkeypatch.setattr(app, "DUMMY_MODE", False)
    monkeypatch.setattr(app, "REPORT_DIR", tmp_path)
    monkeypatch.setattr(app, "MAP_DIR", tmp_path)
    monkeypatch.setattr(app, "geocode_phonenumbers", lambda parsed: "NorthWest")
    monkeypatch.setattr(app, "detect_lada_region", lambda number: "Mexico")
    monkeypatch.setattr(app, "GeoapifyProvider", FakeGeoapifyProvider)
    monkeypatch.setattr(app, "geocode_nominatim", lambda city: (None, None, ""))

    result = app.run_phone_scan("5512345678", {"geoapify": "present_geo"}, ["geoapify"])

    assert "NorthWest" not in geo_calls
    assert result.geoapify_data == {}


def test_tijuana_ift_lada_data_drives_geoapify_query(monkeypatch, tmp_path):
    geo_calls = []

    class FakeGeoapifyProvider:
        def __init__(self, api_key):
            pass

        def lookup(self, locality):
            geo_calls.append(locality)
            return None

    monkeypatch.setattr(app, "DUMMY_MODE", False)
    monkeypatch.setattr(app, "REPORT_DIR", tmp_path)
    monkeypatch.setattr(app, "MAP_DIR", tmp_path)
    monkeypatch.setattr(app, "GeoapifyProvider", FakeGeoapifyProvider)
    monkeypatch.setattr(app, "geocode_nominatim", lambda city: (None, None, ""))

    result = app.run_phone_scan("6634647308", {"geoapify": "present_geo"}, ["geoapify"])

    assert geo_calls == ["Tijuana, Baja California, Mexico"]
    assert result.canonical_locality_query == "Tijuana, Baja California, Mexico"
    assert result.canonical_locality_source == "IFT/PNN exact block + LADA"


def test_opencage_primary_receives_tijuana_query(monkeypatch, tmp_path):
    opencage_calls = []
    geo_calls = []

    class FakeOpenCageProvider:
        def __init__(self, api_key):
            pass

        def lookup(self, locality):
            opencage_calls.append(locality)
            return None

    class FakeGeoapifyProvider:
        def __init__(self, api_key):
            pass

        def lookup(self, locality):
            geo_calls.append(locality)
            return None

    monkeypatch.setattr(app, "DUMMY_MODE", False)
    monkeypatch.setattr(app, "REPORT_DIR", tmp_path)
    monkeypatch.setattr(app, "MAP_DIR", tmp_path)
    monkeypatch.setattr(app, "OpenCageProvider", FakeOpenCageProvider)
    monkeypatch.setattr(app, "GeoapifyProvider", FakeGeoapifyProvider)
    monkeypatch.setattr(app, "geocode_nominatim", lambda city: (None, None, ""))

    app.run_phone_scan("6634647308", {"opencage": "present_open", "geoapify": "present_geo"}, ["opencage", "geoapify"])

    assert opencage_calls == ["Tijuana, Baja California, Mexico"]
    assert geo_calls == ["Tijuana, Baja California, Mexico"]


def test_two_ift_localities_produce_different_geocoding_queries(monkeypatch, tmp_path):
    geo_calls = []

    class FakeGeoapifyProvider:
        def __init__(self, api_key):
            pass

        def lookup(self, locality):
            geo_calls.append(locality)
            return None

    monkeypatch.setattr(app, "DUMMY_MODE", False)
    monkeypatch.setattr(app, "REPORT_DIR", tmp_path)
    monkeypatch.setattr(app, "MAP_DIR", tmp_path)
    monkeypatch.setattr(app, "GeoapifyProvider", FakeGeoapifyProvider)
    monkeypatch.setattr(app, "geocode_nominatim", lambda city: (None, None, ""))

    app.run_phone_scan("5512345678", {"geoapify": "present_geo"}, ["geoapify"])
    app.run_phone_scan("6634647308", {"geoapify": "present_geo"}, ["geoapify"])

    assert geo_calls == [
        "Ciudad de Mexico, Ciudad de Mexico, Mexico",
        "Tijuana, Baja California, Mexico",
    ]


def test_provider_locality_cannot_overwrite_exact_ift_locality(monkeypatch, tmp_path):
    geo_calls = []

    class FakeGeoapifyProvider:
        def __init__(self, api_key):
            pass

        def lookup(self, locality):
            geo_calls.append(locality)
            return None

    monkeypatch.setattr(app, "DUMMY_MODE", False)
    monkeypatch.setattr(app, "REPORT_DIR", tmp_path)
    monkeypatch.setattr(app, "MAP_DIR", tmp_path)
    monkeypatch.setattr(app, "GeoapifyProvider", FakeGeoapifyProvider)
    monkeypatch.setattr(app, "abstract_phone_intelligence_lookup", lambda e164, api_key: {"phone_number": e164})
    monkeypatch.setattr(app, "parse_abstract", lambda data: {"location": "NorthWest", "carrier": "X", "line_type": "mobile"})
    monkeypatch.setattr(app, "numverify_lookup", lambda e164, api_key: {"valid": True})
    monkeypatch.setattr(app, "parse_numverify", lambda data: {"location": "Mexico", "carrier": "Y", "line_type": "mobile"})
    monkeypatch.setattr(app, "geocode_nominatim", lambda city: (None, None, ""))

    result = app.run_phone_scan(
        "6634647308",
        {"geoapify": "present_geo", "abstract_phone_intelligence": "present_abs", "numverify": "present_num"},
        ["geoapify", "abstract_phone_intelligence", "numverify"],
    )

    assert result.consensus_city == "Tijuana, Baja California"
    assert result.canonical_locality_query == "Tijuana, Baja California, Mexico"
    assert geo_calls == ["Tijuana, Baja California, Mexico"]


def test_geocoder_fallbacks_receive_same_canonical_query(monkeypatch, tmp_path):
    calls = {"opencage": [], "geoapify": [], "nominatim": []}

    class FakeOpenCageProvider:
        def __init__(self, api_key):
            pass

        def lookup(self, locality):
            calls["opencage"].append(locality)
            return None

    class FakeGeoapifyProvider:
        def __init__(self, api_key):
            pass

        def lookup(self, locality):
            calls["geoapify"].append(locality)
            return None

    monkeypatch.setattr(app, "DUMMY_MODE", False)
    monkeypatch.setattr(app, "REPORT_DIR", tmp_path)
    monkeypatch.setattr(app, "MAP_DIR", tmp_path)
    monkeypatch.setattr(app, "OpenCageProvider", FakeOpenCageProvider)
    monkeypatch.setattr(app, "GeoapifyProvider", FakeGeoapifyProvider)
    monkeypatch.setattr(app, "geocode_nominatim", lambda city: calls["nominatim"].append(city) or (None, None, ""))

    app.run_phone_scan("6634647308", {"opencage": "present_open", "geoapify": "present_geo"}, ["opencage", "geoapify"])

    assert calls == {
        "opencage": ["Tijuana, Baja California, Mexico"],
        "geoapify": ["Tijuana, Baja California, Mexico"],
        "nominatim": ["Tijuana, Baja California, Mexico"],
    }


def test_plain_output_mentions_evidence_state_once(capsys):
    result = app.ScanResult(e164="+525512345678", consensus_city="Tijuana", evidence_state="single-source result")
    result.all_votes = [app.SourceVote("Tijuana", "phonenumbers", 0.6)]
    result.osint_links = {}

    app.plain_print_consensus(result)
    app.plain_print_geo(result)

    assert capsys.readouterr().out.count("single-source result") == 1
