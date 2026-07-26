"""Authoritative Mexican phone-number normalization."""

from __future__ import annotations

import re
from dataclasses import dataclass

import phonenumbers


@dataclass(frozen=True)
class NormalizedNumber:
    raw_input: str
    national_number: str
    e164: str
    international_digits: str
    detected_format: str
    is_possible: bool
    is_valid: bool
    is_mexican: bool
    parsed: phonenumbers.PhoneNumber | None = None


def _format_hint(raw: str, digits: str) -> str:
    if raw.strip().startswith("+52"):
        return "mx_e164"
    if digits.startswith("52") and len(digits) == 12:
        return "mx_international_digits"
    if len(digits) == 10:
        return "mx_national_10"
    if digits.startswith("521") and len(digits) == 13:
        return "legacy_mx_mobile_prefix"
    if raw.strip().startswith("+"):
        return "international"
    return "unknown"


def normalize_mx_number(raw: str) -> NormalizedNumber:
    """Normalize common Mexican number formats into stable representations."""
    raw_input = "" if raw is None else str(raw)
    stripped = raw_input.strip()
    digits = re.sub(r"\D", "", stripped)
    detected_format = _format_hint(stripped, digits)

    candidate = stripped
    if not candidate.startswith("+"):
        if digits.startswith("00"):
            candidate = f"+{digits[2:]}"
        elif digits.startswith("044") and len(digits) == 13:
            candidate = f"+52{digits[3:]}"
            detected_format = "legacy_044"
        elif digits.startswith("045") and len(digits) == 13:
            candidate = f"+52{digits[3:]}"
            detected_format = "legacy_045"
        elif digits.startswith("01") and len(digits) == 12:
            candidate = f"+52{digits[2:]}"
            detected_format = "legacy_01"
        elif digits.startswith("52"):
            candidate = f"+{digits}"
        elif len(digits) == 10:
            candidate = f"+52{digits}"
        else:
            candidate = f"+{digits}"

    try:
        parsed = phonenumbers.parse(candidate, None)
    except phonenumbers.NumberParseException:
        return NormalizedNumber(
            raw_input=raw_input,
            national_number="",
            e164="",
            international_digits=digits,
            detected_format=detected_format,
            is_possible=False,
            is_valid=False,
            is_mexican=False,
            parsed=None,
        )

    e164 = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    national = str(parsed.national_number)
    if parsed.country_code == 52 and len(national) == 11 and national.startswith("1"):
        national = national[1:]
        e164 = f"+52{national}"

    return NormalizedNumber(
        raw_input=raw_input,
        national_number=national if parsed.country_code == 52 else str(parsed.national_number),
        e164=e164,
        international_digits=e164.replace("+", ""),
        detected_format=detected_format,
        is_possible=phonenumbers.is_possible_number(parsed),
        is_valid=phonenumbers.is_valid_number(parsed),
        is_mexican=parsed.country_code == 52 and len(national) == 10,
        parsed=parsed,
    )
