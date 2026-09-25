from mexicosint.main import _read_batch_numbers
from mexicosint.core.scan_result import ScanResult
from mexicosint.core.settings import ScanSettings
from mexicosint.reporting import save_batch_exports


def test_read_batch_numbers_ignores_comments_and_blank_lines(tmp_path):
    batch = tmp_path / "numbers.txt"
    batch.write_text("# comment\n\n5512345678\n+525512345678 extra\n", encoding="utf-8")

    assert _read_batch_numbers(str(batch)) == ["5512345678", "+525512345678"]


def test_save_batch_exports_writes_manifest_and_csv(tmp_path):
    result = ScanResult(
        scan_id="MX-TEST",
        e164="+525512345678",
        valid=True,
        ift_carrier="Telcel",
        consensus_city="Ciudad de Mexico",
    )
    result.finalize_mexico_data_trust()

    manifest_path, csv_path = save_batch_exports(
        [result],
        "numbers.txt",
        ScanSettings(output_dir=tmp_path),
    )

    assert manifest_path.endswith(".json")
    assert csv_path.endswith(".csv")
    assert "MX-TEST" in open(manifest_path, encoding="utf-8").read()
    assert "+525512345678" in open(csv_path, encoding="utf-8").read()


def test_read_batch_numbers_requires_a_file(tmp_path):
    try:
        _read_batch_numbers(str(tmp_path / "missing.txt"))
    except FileNotFoundError:
        return
    raise AssertionError("missing batch file should raise FileNotFoundError")
