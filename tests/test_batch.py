from mexicosint.main import _read_batch_numbers


def test_read_batch_numbers_ignores_comments_and_blank_lines(tmp_path):
    batch = tmp_path / "numbers.txt"
    batch.write_text("# comment\n\n5512345678\n+525512345678 extra\n", encoding="utf-8")

    assert _read_batch_numbers(str(batch)) == ["5512345678", "+525512345678"]


def test_read_batch_numbers_requires_a_file(tmp_path):
    try:
        _read_batch_numbers(str(tmp_path / "missing.txt"))
    except FileNotFoundError:
        return
    raise AssertionError("missing batch file should raise FileNotFoundError")
