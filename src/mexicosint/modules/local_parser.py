#!/usr/bin/env python3
"""
local_parser.py
Zero-network Mexican phone number parsing.
Uses phonenumbers lib + hardcoded MNC/LADA tables.
"""

import phonenumbers
from phonenumbers import geocoder, carrier, timezone, PhoneNumberType

from mexicosint.data.lada import LADA_MAP

# Mexico MNC → Carrier mapping
MNC_CARRIERS = {
    "010": "Telcel (América Móvil)",
    "020": "Telcel (América Móvil)",
    "030": "Movistar (Telefónica)",
    "040": "Unefon (AT&T)",
    "050": "Unefon (AT&T)",
    "060": "Unefon (AT&T)",
    "070": "AT&T Mexico",
    "080": "Unefon (AT&T)",
    "090": "AT&T Mexico",
    "100": "AT&T Mexico",
    "140": "Altán Redes (Red Compartida)",
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

    # Strip common noise
    cleaned = raw.strip().replace("-", "").replace(" ", "").replace("(", "").replace(")", "")
    
    # Handle numbers that already include +52 or 52 prefix
    if cleaned.startswith("+52"):
        cleaned = cleaned[3:]
    elif cleaned.startswith("52"):
        cleaned = cleaned[2:]
    
    # Handle the '1' mobile prefix (post-2019 reform: +52 1 AA XXXX XXXX)
    if len(cleaned) == 11 and cleaned.startswith("1"):
        cleaned = cleaned[1:]
    
    # Must be exactly 10 digits now
    if not cleaned.isdigit() or len(cleaned) != 10:
        result["error"] = f"Invalid length or characters after cleaning: {cleaned}"
        return result

    result["normalized_10"] = cleaned
    result["e164"] = f"+52{cleaned}"
    result["is_valid"] = True

    # Extract LADA (first 2 or 3 digits)
    lada_3 = cleaned[:3]
    lada_2 = cleaned[:2]
    
    if lada_3 in LADA_MAP:
        result["lada"] = lada_3
        result["city"], result["state"] = LADA_MAP[lada_3]
    elif lada_2 in LADA_MAP:
        result["lada"] = lada_2
        result["city"], result["state"] = LADA_MAP[lada_2]
    else:
        result["lada"] = lada_2  # fallback

    # Use phonenumbers library for deeper parsing
    try:
        parsed = phonenumbers.parse(result["e164"], None)
        result["is_valid"] = phonenumbers.is_valid_number(parsed)
        
        num_type = phonenumbers.number_type(parsed)
        result["number_type"] = TYPE_MAP.get(num_type, f"UNKNOWN_ENUM({num_type})")
        
        # In Mexico, FIXED_LINE_OR_MOBILE means "could be either" but in practice
        # nearly all 10-digit numbers are mobile. We flag it as likely mobile.
        if num_type == PhoneNumberType.MOBILE:
            result["is_mobile"] = True
        elif num_type == PhoneNumberType.FIXED_LINE_OR_MOBILE:
            result["is_mobile"] = True  # Mexico reality: almost certainly mobile
        elif num_type == PhoneNumberType.FIXED_LINE:
            result["is_mobile"] = False
        else:
            result["is_mobile"] = False
            
        # Timezone
        tz = timezone.time_zones_for_number(parsed)
        result["timezone"] = list(tz) if tz else []
        
        # Carrier from phonenumbers (best-effort, often generic for MX)
        carrier_name = carrier.name_for_number(parsed, "es")
        if carrier_name:
            result["carrier_hint"] = carrier_name
            
    except Exception as e:
        result["phonenumbers_error"] = str(e)

    return result


if __name__ == "__main__":
    import sys
    test = sys.argv[1] if len(sys.argv) > 1 else "5512345678"
    import json
    print(json.dumps(parse_mx_number(test), indent=2, ensure_ascii=False))
