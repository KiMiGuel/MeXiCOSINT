from mexicosint.core.scan_result import ScanResult
from mexicosint.core.settings import ScanSettings
from mexicosint.history import diff_scan_summaries, load_history, record_scan


def test_history_records_and_loads_scan_summaries(tmp_path):
    settings = ScanSettings(output_dir=tmp_path)
    result = ScanResult(
        scan_id="MX-ONE",
        e164="+525512345678",
        valid=True,
        ift_carrier="Telcel",
        consensus_city="Ciudad de Mexico",
    )
    result.finalize_mexico_data_trust()

    path = record_scan(result, settings)
    history = load_history(settings)

    assert path.endswith("history.jsonl")
    assert len(history) == 1
    assert history[0]["scan_id"] == "MX-ONE"
    assert history[0]["ift_carrier"] == "Telcel"


def test_diff_scan_summaries_reports_changed_evidence():
    changes = diff_scan_summaries(
        {"valid": True, "ift_carrier": "Telcel", "latitude": 19.4},
        {"valid": True, "ift_carrier": "Movistar", "latitude": 19.4},
    )

    assert changes == {
        "ift_carrier": {"before": "Telcel", "after": "Movistar"}
    }
