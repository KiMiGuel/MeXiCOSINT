import pytest

from mexicosint.numbering import normalize_mx_number


@pytest.mark.parametrize(
    "raw",
    [
        "+526634647308",
        "526634647308",
        "6634647308",
        "+52 663 464 7308",
        "52-663-464-7308",
        "(663) 464-7308",
    ],
)
def test_normalize_supported_mexican_formats(raw):
    normalized = normalize_mx_number(raw)

    assert normalized.raw_input == raw
    assert normalized.national_number == "6634647308"
    assert normalized.e164 == "+526634647308"
    assert normalized.international_digits == "526634647308"
    assert normalized.is_possible is True
    assert normalized.is_valid is True
    assert normalized.is_mexican is True
    assert normalized.detected_format


def test_normalize_rejects_non_mexican_number():
    normalized = normalize_mx_number("+14155552671")

    assert normalized.is_mexican is False
    assert normalized.e164 == "+14155552671"
