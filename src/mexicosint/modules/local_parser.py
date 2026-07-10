#!/usr/bin/env python3
"""
local_parser.py
Zero-network Mexican phone number parsing.
Uses phonenumbers lib + hardcoded MNC/LADA tables.
"""

from typing import Optional

import phonenumbers
from phonenumbers import geocoder, carrier, timezone, PhoneNumberType

# Mexico MNC -> Carrier mapping
MNC_CARRIERS = {
    "010": "Telcel (America Movil)",
    "020": "Telcel (America Movil)",
    "030": "Movistar (Telefonica)",
    "040": "Unefon (AT&T)",
    "050": "Unefon (AT&T)",
    "060": "Unefon (AT&T)",
    "070": "AT&T Mexico",
    "080": "Unefon (AT&T)",
    "090": "AT&T Mexico",
    "100": "AT&T Mexico",
    "140": "Altan Redes (Red Compartida)",
    "150": "Ultra Wey (MVNO)",
    "160": "Maz Tiempo (MVNO)",
}

# Human-readable type mapping
TYPE_MAP = {
    PhoneNumberType.FIXED_LINE: "FIXED_LINE",
    PhoneNumberType.MOBILE: "MOBILE",
    PhoneNumberType.FIXED_LINE_OR_MOBILE: "FIXED_LINE_OR_MOBILE",
    PhoneNumberType.TOLL_FREE: "TOLL_FREE",
    PhoneNumberType.PREMIUM_RATE: "PREMIUM_RATE",
    PhoneNumberType.SHARED_COST: "SHARED_COST",
    PhoneNumberType.VOIP: "VOIP",
    PhoneNumberType.PERSONAL_NUMBER: "PERSONAL_NUMBER",
    PhoneNumberType.PAGER: "PAGER",
    PhoneNumberType.UAN: "UAN",
    PhoneNumberType.UNKNOWN: "UNKNOWN",
}

# Major LADA -> State/City mapping
LADA_MAP = {
    "55": ("Ciudad de Mexico", "CDMX"),
    "56": ("Ciudad de Mexico", "CDMX"),
    "81": ("Monterrey", "Nuevo Leon"),
    "33": ("Guadalajara", "Jalisco"),
    "222": ("Puebla", "Puebla"),
    "999": ("Merida", "Yucatan"),
    "442": ("Queretaro", "Queretaro"),
    "686": ("Mexicali", "Baja California"),
    "663": ("Tijuana", "Baja California"),
    "664": ("Tijuana", "Baja California"),
    "618": ("Durango", "Durango"),
    "449": ("Aguascalientes", "Aguascalientes"),
    "229": ("Veracruz", "Veracruz"),
    "938": ("Villahermosa", "Tabasco"),
    "983": ("Chetumal", "Quintana Roo"),
    "871": ("Torreon", "Coahuila"),
    "844": ("Saltillo", "Coahuila"),
    "477": ("Leon", "Guanajuato"),
    "722": ("Toluca", "Mexico"),
    "246": ("Tlaxcala", "Tlaxcala"),
    "312": ("Colima", "Colima"),
    "322": ("Puerto Vallarta", "Jalisco"),
    "667": ("Culiacan", "Sinaloa"),
    "668": ("Mazatlan", "Sinaloa"),
    "631": ("Nogales", "Sonora"),
    "662": ("Hermosillo", "Sonora"),
    "961": ("Tuxtla Gutierrez", "Chiapas"),
    "962": ("Tapachula", "Chiapas"),
    "735": ("Cuernavaca", "Morelos"),
    "771": ("Pachuca", "Hidalgo"),
    "773": ("Tulancingo", "Hidalgo"),
    "747": ("Chilpancingo", "Guerrero"),
    "753": ("Lazaro Cardenas", "Michoacan"),
    "443": ("Morelia", "Michoacan"),
    "341": ("Ciudad Guzman", "Jalisco"),
    "834": ("Tampico", "Tamaulipas"),
    "899": ("Reynosa", "Tamaulipas"),
    "867": ("Nuevo Laredo", "Tamaulipas"),
}


def parse_mx_number(raw: str) -> dict:
    """
    Normalize and parse a Mexican phone number.
    Input: raw string (e.g., '+52 1 55 1234 5678', '5512345678', '55-1234-5678')
    Returns: dict with normalized 10-digit number, E164, LADA, state, city,
             carrier hint, timezone, is_valid, number_type, is_mobile
    """
    result = {
        "input": raw,
        "normalized_10": None,
        "e164": None,
        "lada": None,
        "city": "Unknown",
        "state": "Unknown",
        "carrier_hint": "Unknown",
        "timezone": [],
        "number_type": "Unknown",
        "is_valid": False,
        "is_mobile": False,
    }

    cleaned = raw.strip().replace("-", "").replace(" ", "").replace("(", "").replace(")", "")

    if cleaned.startswith("+52"):
        cleaned = cleaned[3:]
    elif cleaned.startswith("52"):
        cleaned = cleaned[2:]

    if len(cleaned) == 11 and cleaned.startswith("1"):
        cleaned = cleaned[1:]

    if not cleaned.isdigit() or len(cleaned) != 10:
        result["error"] = f"Invalid length or characters after cleaning: {cleaned}"
        return result

    result["normalized_10"] = cleaned
    result["e164"] = f"+52{cleaned}"
    result["is_valid"] = True

    lada_3 = cleaned[:3]
    lada_2 = cleaned[:2]

    if lada_3 in LADA_MAP:
        result["lada"] = lada_3
        result["city"], result["state"] = LADA_MAP[lada_3]
    elif lada_2 in LADA_MAP:
        result["lada"] = lada_2
        result["city"], result["state"] = LADA_MAP[lada_2]
    else:
        result["lada"] = lada_2

    try:
        parsed = phonenumbers.parse(result["e164"], None)
        result["is_valid"] = phonenumbers.is_valid_number(parsed)

        num_type = phonenumbers.number_type(parsed)
        result["number_type"] = TYPE_MAP.get(num_type, f"UNKNOWN_ENUM({num_type})")

        if num_type == PhoneNumberType.MOBILE:
            result["is_mobile"] = True
        elif num_type == PhoneNumberType.FIXED_LINE_OR_MOBILE:
            result["is_mobile"] = True
        elif num_type == PhoneNumberType.FIXED_LINE:
            result["is_mobile"] = False
        else:
            result["is_mobile"] = False

        tz = timezone.time_zones_for_number(parsed)
        result["timezone"] = list(tz) if tz else []

        carrier_name = carrier.name_for_number(parsed, "es")
        if carrier_name:
            result["carrier_hint"] = carrier_name

    except Exception as e:
        result["phonenumbers_error"] = str(e)

    return result


def _extract_label_value(*_args, **_kwargs) -> Optional[str]:
    return None


if __name__ == "__main__":
    import json
    import sys

    test = sys.argv[1] if len(sys.argv) > 1 else "5512345678"
    print(json.dumps(parse_mx_number(test), indent=2, ensure_ascii=False))
