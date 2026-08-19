#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MeXicOSINT v2.5.2
Herramienta de OSINT para numeros telefonicos Mexicanos
Autor: KiMiGuEL

Cambios v2.5.2:
  - Proveedor Google Places removido (friccion de billing/API key sin beneficio claro)
  - Diagnostico de errores de Google Places corregido antes del removido (ya no aplica)

Cambios v2.5.1:
  - Normalizador mexicano compartido
  - Geoapify como geocodificador de localidad de numeracion
  - Google Places e IPQualityScore agregados como proveedores opcionales
  - Modo IP y proveedores IP removidos

Cambios anteriores:
  - Base oficial IFT/PNN integrada (178k bloques de numeracion)
  - Consulta offline de operadora, modalidad y fecha de asignacion
  - Identificacion de series no geograficas 200/300/500/800/900
  - Alerta de fraude para numeros 900 (cobro premium)
  - Herramienta tools/update_ift_blocks.py para actualizar la base

Correcciones v2.2.4:
  - Validacion usa is_valid_number() ademas de is_possible_number()
  - Calculo de confianza requiere al menos 2 fuentes para 95%
  - Timestamp usa default_factory para evitar valor estatico
  - Base LADA actualizada con datos oficiales IFT (2024)
  - Portabilidad corregida: implementada en 2008, marcado a 10 digitos en 2019
  - Abstract Phone Intelligence y Phone Validation usan keys separadas
  - Reporte JSON limpio: excluye report_path y report_hash del payload
  - Links OSINT corregidos: solo enlaces que realmente buscan por numero
  - Config ahora crea archivo con permisos 0o600 (solo lectura propietario)
"""

import requests
import sys
import json
import re
import urllib.parse
import hashlib
import uuid
import unicodedata
import copy
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict

from mexicosint import config as config_store
from mexicosint.evidence import SourceVote, decide_evidence, normalize_city
from mexicosint.numbering import normalize_mx_number
from mexicosint.modules.local_parser import parse_mx_number
from mexicosint.providers.geoapify import GeoapifyProvider
from mexicosint.providers.ipqualityscore import IPQualityScoreProvider
from mexicosint.providers.opencage import OpenCageProvider

try:
    from mexicosint.modules.ift_blocks import lookup_block, modality_label
    IFT_BLOCKS_AVAILABLE = True
except ImportError:
    IFT_BLOCKS_AVAILABLE = False

try:
    from rich.console import Console
    from rich.table import Table
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

CONFIG_PATH = config_store.CONFIG_PATH
OUTPUT_DIR = Path("output")
REPORT_DIR = OUTPUT_DIR / "reports"
MAP_DIR = OUTPUT_DIR / "maps"
for d in (REPORT_DIR, MAP_DIR):
    d.mkdir(parents=True, exist_ok=True)

SAMPLE_CONFIG = config_store.SAMPLE_CONFIG

DUMMY_MODE = False
SMALL_BANNER = False


def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


@dataclass
class ScanResult:
    scan_id: str = ""
    raw_input: str = ""
    detected_format: str = ""
    international_digits: str = ""
    is_possible: bool = False
    is_mexican: bool = False
    e164: str = ""
    valid: bool = False
    country_code: str = ""
    national_number: str = ""
    region_phonenumbers: str = ""
    lada_region: str = ""
    ift_carrier: str = ""
    ift_modality: str = ""
    ift_zona: str = ""
    ift_fecha_asignacion: str = ""
    ift_service_type: str = ""
    canonical_locality_city: str = ""
    canonical_locality_state: str = ""
    canonical_locality_query: str = ""
    canonical_locality_source: str = ""
    abstract_data: dict = field(default_factory=dict)
    numverify_data: dict = field(default_factory=dict)
    abstract_location: str = ""
    numverify_location: str = ""
    abstract_carrier: str = ""
    numverify_carrier: str = ""
    abstract_line_type: str = ""
    numverify_line_type: str = ""
    consensus_city: str = ""
    consensus_confidence: float = 0.0
    consensus_sources: list = field(default_factory=list)
    evidence_state: str = "no usable locality"
    all_votes: list = field(default_factory=list)
    latitude: float = None
    longitude: float = None
    nominatim_address: str = ""
    opencage_data: dict = field(default_factory=dict)
    opencage_latitude: float = None
    opencage_longitude: float = None
    opencage_address: str = ""
    geoapify_data: dict = field(default_factory=dict)
    geoapify_latitude: float = None
    geoapify_longitude: float = None
    geoapify_address: str = ""
    ipqualityscore_data: dict = field(default_factory=dict)
    provider_trace: list = field(default_factory=list)
    osint_links: dict = field(default_factory=dict)
    map_path: str = ""
    report_path: str = ""
    report_hash: str = ""
    errors: list = field(default_factory=list)
    # FIX #3: Use default_factory instead of direct function call
    scan_timestamp: str = field(default_factory=_now_utc)

    def to_dict(self):
        return asdict(self)

    def to_report_dict(self):
        """Return dict for JSON export, excluding internal report fields."""
        data = self.to_dict()
        # FIX #7: Remove report_path and report_hash from payload before hashing
        data.pop("report_path", None)
        data.pop("report_hash", None)
        return data


# --- SAMPLE DATA (DUMMY MODE) ---
SAMPLE_ABSTRACT_INTEL = {
    "phone_number": "+525512345678",
    "phone_format": {"international": "+52 55 1234 5678", "national": "(55) 1234-5678"},
    "phone_carrier": {"name": "Telcel", "line_type": "mobile", "mcc": 334, "mnc": 20},
    "phone_location": {
        "country_name": "Mexico",
        "country_code": "MX",
        "country_prefix": "+52",
        "region": "Ciudad de Mexico",
        "city": "Ciudad de Mexico",
        "timezone": "America/Mexico_City"
    },
    "phone_validation": {"is_valid": True, "line_status": "active", "is_voip": False},
    "phone_risk": {"risk_level": "low", "is_disposable": False, "is_abuse_detected": False}
}

SAMPLE_NUMVERIFY = {
    "valid": True,
    "local_format": "5512345678",
    "international_format": "+525512345678",
    "country_name": "Mexico",
    "country_code": "MX",
    "location": "Mexico City",
    "carrier": "Telcel",
    "line_type": "mobile"
}

SAMPLE_GEOAPIFY = {
    "source": "Geoapify",
    "kind": "numbering_locality",
    "city": "Ciudad de Mexico",
    "state": "Ciudad de Mexico",
    "country": "Mexico",
    "country_code": "MX",
    "formatted_address": "Ciudad de Mexico, Mexico",
    "latitude": None,
    "longitude": None,
    "note": "Numbering locality only; not live phone or subscriber location.",
}

SAMPLE_IPQUALITYSCORE = {
    "source": "IPQualityScore",
    "valid": True,
    "active": True,
    "risk_score": 10,
    "abuse_recent": False,
    "voip": False,
    "carrier": "Telcel",
    "line_type": "Wireless",
    "country_code": "MX",
    "city": "Ciudad de Mexico",
    "region": "Ciudad de Mexico",
}

# --- BANNER ---
GREEN = '\033[1;32m'
WHITE = '\033[1;37m'
RED = '\033[1;31m'
RESET = '\033[0m'


def _render_figlet(text, font_arg):
    import subprocess
    try:
        result = subprocess.run(
            ["figlet", "-f", font_arg, text],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return result.stdout.rstrip().splitlines()
    except Exception:
        pass
    return None


def print_banner():
    import shutil
    try:
        term_width = shutil.get_terminal_size().columns
    except Exception:
        term_width = 80

    # Default to small font; Bloody font is too wide and breaks the banner
    if SMALL_BANNER:
        fonts_to_try = [("small", "small")]
    else:
        fonts_to_try = [("small", "small"), ("standard", "standard")]

    chosen_lines = None
    chosen_name = None
    for name, font_arg in fonts_to_try:
        lines = _render_figlet("MeXicOSINT", font_arg)
        if not lines:
            continue
        width = max(len(line) for line in lines)
        if not SMALL_BANNER and width > term_width - 8:
            continue
        chosen_lines = lines
        chosen_name = name
        break

    if chosen_lines:
        lines = chosen_lines
        max_width = max(len(line) for line in lines)
        if max_width > term_width - 4:
            max_width = term_width - 4
        border = GREEN + "╔" + "═" * (max_width + 4) + "╗" + RESET
        bottom = RED + "╚" + "═" * (max_width + 4) + "╝" + RESET
        print()
        print(border)
        for line in lines:
            line = line[:max_width]
            padding = max_width - len(line)
            third = len(line) // 3
            left = line[:third]
            mid = line[third:2*third]
            right = line[2*third:]
            colored = f"{GREEN}{left}{WHITE}{mid}{RED}{right}{RESET}"
            print(f"{GREEN}║  {colored}{' ' * padding}  {RED}║{RESET}")
        print(bottom)
        print(f"{WHITE}         OSINT para numeros telefonicos Mexicanos{RESET}")
        print(f"{RED}                   Autor: KiMiGuEL{RESET}")
        print()
        return

    print()
    print(GREEN + "╔══════════════════════════════════════════════════════════════════╗" + RESET)
    print(GREEN + "║                                                                  ║" + RESET)
    print(WHITE + "║                    MeXicOSINT v2.5.1                             ║" + RESET)
    print(RED + "║              OSINT para numeros Mexicanos                        ║" + RESET)
    print(RED + "║                    Autor: KiMiGuEL                               ║" + RESET)
    print(RED + "╚══════════════════════════════════════════════════════════════════╝" + RESET)
    print()


def init_config():
    return config_store.init_config(CONFIG_PATH, DUMMY_MODE)


def check_keys(config):
    return config_store.check_keys(config, DUMMY_MODE)


def _get_api_key(config, key):
    return config_store.get_api_key(config, key)


# --- API KEY MANAGEMENT (CLI) ---
SERVICE_ALIASES = config_store.SERVICE_ALIASES


def _canonical_service(name: str) -> str:
    return config_store.canonical_service(name)


def _mask_key(value: str) -> str:
    return config_store.mask_key(value)


def set_key_cli(service: str, key: str) -> int:
    return config_store.set_key(service, key, CONFIG_PATH)


def list_keys_cli() -> int:
    return config_store.list_keys(CONFIG_PATH)


# --- MEXICO LADA DATABASE (FIX #4: Official IFT data) ---
# Source: Instituto Federal de Telecomunicaciones (IFT) - Plan Nacional de Numeracion
# https://www.ift.org.mx/plan-nacional-de-numeracion
# Mobile numbering: 1 + 10 digits. LADA prefixes for geographic areas.
# NOTE: Due to number portability (since 2008), LADA is only a historical reference.
LADA_MAP = {
    "55": "Ciudad de Mexico",
    "81": "Monterrey, Nuevo Leon",
    "33": "Guadalajara, Jalisco",
    "646": "Ensenada, Baja California",
    "661": "Tecate, Baja California",
    "664": "Tijuana, Baja California",
    "665": "Tijuana, Baja California",
    "686": "Mexicali, Baja California",
    "612": "La Paz, Baja California Sur",
    "624": "Los Cabos, Baja California Sur",
    "981": "Campeche, Campeche",
    "938": "Ciudad del Carmen, Campeche",
    "614": "Chihuahua, Chihuahua",
    "625": "Ciudad Cuauhtemoc, Chihuahua",
    "639": "Ciudad Delicias, Chihuahua",
    "656": "Ciudad Juarez, Chihuahua",
    "627": "Parral, Chihuahua",
    "844": "Saltillo, Coahuila",
    "861": "Sabinas, Coahuila",
    "866": "Monclova, Coahuila",
    "871": "Torreon, Coahuila",
    "878": "Piedras Negras, Coahuila",
    "312": "Colima, Colima",
    "314": "Manzanillo, Colima",
    "961": "Tuxtla Gutierrez, Chiapas",
    "962": "Tapachula, Chiapas",
    "618": "Durango, Durango",
    "415": "San Miguel de Allende, Guanajuato",
    "427": "Polotitlan, Guanajuato",
    "445": "Moroleon, Guanajuato",
    "462": "Irapuato, Guanajuato",
    "464": "Salamanca, Guanajuato",
    "473": "Guanajuato, Guanajuato",
    "477": "Leon, Guanajuato",
    "733": "Mayanalan, Guerrero",
    "747": "Chilpancingo, Guerrero",
    "755": "Zihuatanejo, Guerrero",
    "771": "Pachuca, Hidalgo",
    "773": "Tepeji del Rio, Hidalgo",
    "775": "Singuilucan, Hidalgo",
    "341": "Ciudad Guzman, Jalisco",
    "378": "Tepatitlan, Jalisco",
    "392": "Ocotlan, Jalisco",
    "474": "Lagos de Moreno, Jalisco",
    "594": "San Marcos Nepantla, Estado de Mexico",
    "595": "Texcoco, Estado de Mexico",
    "722": "Toluca, Estado de Mexico",
    "728": "Lerma, Estado de Mexico",
    "352": "La Piedad, Michoacan",
    "353": "Sahuayo, Michoacan",
    "351": "Zamora, Michoacan",
    "443": "Morelia, Michoacan",
    "452": "Uruapan, Michoacan",
    "734": "Zacatepec, Morelos",
    "735": "Cuautla, Morelos",
    "777": "Cuernavaca, Morelos",
    "311": "Tepic, Nayarit",
    "951": "Oaxaca, Oaxaca",
    "971": "Ixtepec, Oaxaca",
    "222": "Puebla, Puebla",
    "238": "Tehuacan, Puebla",
    "248": "San Martin Texmelucan, Puebla",
    "442": "Queretaro, Queretaro",
    "983": "Chetumal, Quintana Roo",
    "998": "Cancun, Quintana Roo",
    "444": "San Luis Potosi, San Luis Potosi",
    "481": "Ciudad Valles, San Luis Potosi",
    "667": "Culiacan, Sinaloa",
    "668": "Los Mochis, Sinaloa",
    "669": "Mazatlan, Sinaloa",
    "622": "Guaymas, Sonora",
    "631": "Nogales, Sonora",
    "642": "Navojoa, Sonora",
    "644": "Ciudad Obregon, Sonora",
    "653": "San Luis Rio Colorado, Sonora",
    "662": "Hermosillo, Sonora",
    "993": "Villahermosa, Tabasco",
    "831": "Ciudad Mante, Tamaulipas",
    "833": "Tampico, Tamaulipas",
    "834": "Ciudad Victoria, Tamaulipas",
    "867": "Nuevo Laredo, Tamaulipas",
    "868": "Matamoros, Tamaulipas",
    "899": "Reynosa, Tamaulipas",
    "241": "Apizaco, Tlaxcala",
    "246": "Tlaxcala, Tlaxcala",
    "228": "Jalapa, Veracruz",
    "229": "Veracruz, Veracruz",
    "271": "Cordoba, Veracruz",
    "272": "Orizaba, Veracruz",
    "783": "Tuxpan, Veracruz",
    "921": "Coatzacoalcos, Veracruz",
    "922": "Chinameca, Veracruz",
    "999": "Merida, Yucatan",
    "492": "Zacatecas, Zacatecas",
    "493": "Fresnillo, Zacatecas",
}

def detect_lada_region(national_number: str) -> str:
    nat = national_number.replace(" ", "")
    if len(nat) < 10:
        return ""
    # Mobile numbers in Mexico: 1 + 10 digits after +52
    # If national number starts with 1, skip it for LADA
    if nat.startswith("1") and len(nat) == 11:
        nat = nat[1:]
    lada3 = nat[:3]
    lada2 = nat[:2]
    return LADA_MAP.get(lada3) or LADA_MAP.get(lada2) or ""


# --- VALIDATION ---
# FIX #1: Add is_valid_number() in addition to is_possible_number()
def validate_mx_number(raw):
    normalized = normalize_mx_number(raw)
    if not normalized.is_possible:
        print(f"[!] ERROR: '{raw}' no es un numero posible.")
        return None
    if not normalized.is_valid:
        print(f"[!] ERROR: '{raw}' no es un numero valido (posible pero no valido).")
        return None
    if not normalized.is_mexican:
        parsed = normalized.parsed
        code = parsed.country_code if parsed else "desconocido"
        print(f"[!] ERROR: Codigo de pais {code}, se esperaba 52 (Mexico).")
        return None
    return normalized.e164, normalized.parsed


# --- GEOCODER PHONENUMBERS ---
def geocode_phonenumbers(parsed):
    try:
        from phonenumbers import geocoder
        region = geocoder.description_for_number(parsed, "es")
        return region
    except Exception:
        return None


# --- NOMINATIM GEOCODING ---
# Vague/generic locations that should NOT be geocoded (false positive prevention)
VAGUE_LOCATIONS = {
    "unknown", "mexico", "méxico", "unknown city",
    "n/a", "not found", "sin informacion", "no hay informacion",
    "desconocido", "indefinido", "general", "nacional", "republica mexicana",
    "estados unidos mexicanos",
}
GENERIC_LOCALITIES = {
    "northwest", "north west", "noroeste", "noroeste de mexico",
    "northeast", "north east", "noreste", "noreste de mexico",
    "central", "centro", "sur", "south", "southeast", "south east", "sureste",
    "southwest", "south west", "suroeste", "baja california", "baja california sur",
    "sonora", "chihuahua", "coahuila", "nuevo leon", "tamaulipas", "sinaloa",
    "durango", "zacatecas", "jalisco", "colima", "michoacan", "guanajuato",
    "queretaro", "hidalgo", "estado de mexico", "morelos", "puebla", "tlaxcala",
    "veracruz", "guerrero", "oaxaca", "chiapas", "tabasco", "campeche",
    "yucatan", "quintana roo", "aguascalientes", "nayarit", "san luis potosi",
}

def _normalize_for_vague(city_region: str) -> str:
    """Normalize string for VAGUE_LOCATIONS comparison (accents, lowercase, strip)."""
    city_region = city_region.lower().strip()
    city_region = unicodedata.normalize('NFKD', city_region).encode('ASCII', 'ignore').decode('ASCII')
    return city_region


def _is_concrete_locality(city_region: str) -> bool:
    if not city_region:
        return False
    normalized = _normalize_for_vague(city_region)
    normalized = re.sub(r"[^a-z0-9\s,]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    compact = normalized.replace(",", " ").strip()
    if not compact:
        return False
    if compact in VAGUE_LOCATIONS or compact in GENERIC_LOCALITIES:
        return False
    return any(char.isalpha() for char in compact) and len(compact) >= 3


def _clean_place_name(value: str) -> str:
    value = (value or "").strip()
    if not value or value.lower() == "unknown":
        return ""
    value = unicodedata.normalize("NFKD", value).encode("ASCII", "ignore").decode("ASCII")
    aliases = {
        "CDMX": "Ciudad de Mexico",
        "Distrito Federal": "Ciudad de Mexico",
        "Mexico City": "Ciudad de Mexico",
    }
    return aliases.get(value, value)


def _split_lada_region(region: str) -> tuple[str, str]:
    if not region or "," not in region:
        return "", ""
    city, state = [part.strip() for part in region.split(",", 1)]
    return _clean_place_name(city), _clean_place_name(state)


def _set_canonical_locality(result: ScanResult, local_info: dict, has_ift_block: bool) -> None:
    city = _clean_place_name(local_info.get("city", ""))
    state = _clean_place_name(local_info.get("state", ""))
    if not city or not state:
        city, state = _split_lada_region(result.lada_region)
    locality = f"{city}, {state}" if city and state else ""
    if not _is_concrete_locality(locality):
        return
    result.canonical_locality_city = city
    result.canonical_locality_state = state
    result.canonical_locality_query = f"{city}, {state}, Mexico"
    result.canonical_locality_source = "IFT/PNN exact block + LADA" if has_ift_block else "LADA"


def _locality_compare_key(value: str) -> str:
    value = value or ""
    first = value.split(",", 1)[0].strip()
    return normalize_city(first or value)


def _trace_provider(result: ScanResult, provider: str, status: str, normalized, locality_query: str = "", note: str = ""):
    entry = {
        "provider": provider,
        "status": status,
        "e164": normalized.e164,
        "international_digits": normalized.international_digits,
    }
    if locality_query:
        entry["locality_query"] = locality_query
    if note:
        entry["note"] = note
    result.provider_trace.append(entry)
    detail = f" input={normalized.e164}"
    if locality_query:
        detail += f" locality={locality_query}"
    if note:
        detail += f" note={note}"
    print(f"    [trace] {provider}: {status}{detail}")


def _lookup_cached_geocoder(provider, locality: str):
    lookup = provider.lookup
    before = lookup.cache_info() if hasattr(lookup, "cache_info") else None
    evidence = lookup(locality)
    after = lookup.cache_info() if hasattr(lookup, "cache_info") else None
    status = "live_request"
    if before and after:
        status = "cache_hit" if after.hits > before.hits else "cache_miss"
    return evidence, status

def geocode_nominatim(city_region):
    if not _is_concrete_locality(city_region):
        return None, None, ""
    if DUMMY_MODE:
        return None, None, ""
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": f"{city_region}, Mexico",
            "format": "json",
            "limit": 1,
            "countrycodes": "mx"
        }
        headers = {"User-Agent": "MeXicOSINT/2.5.1 (OSINT research)"}
        r = requests.get(url, params=params, headers=headers, timeout=10)
        data = r.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"]), data[0].get("display_name", "")
    except Exception:
        pass
    return None, None, ""


# --- API CALLS ---
def abstract_phone_intelligence_lookup(e164, api_key):
    if DUMMY_MODE:
        return copy.deepcopy(SAMPLE_ABSTRACT_INTEL)

    url = "https://phoneintelligence.abstractapi.com/v1/"
    params = {"api_key": api_key, "phone": e164}

    try:
        r = requests.get(url, params=params, timeout=15)
        if r.status_code == 200:
            data = r.json()
            if "phone_number" in data or "phone" in data or "format" in data:
                return data
    except requests.RequestException as e:
        status = getattr(e.response, 'status_code', 'N/A') if hasattr(e, 'response') else 'N/A'
        text = getattr(e.response, 'text', 'N/A')[:200] if hasattr(e, 'response') else 'N/A'
        raise Exception(f"Abstract Phone Intelligence API: HTTP {status} - {text} - {e}")

    raise Exception("Abstract Phone Intelligence API: endpoint fallo (sin respuesta valida)")


def numverify_lookup(e164, api_key):
    if DUMMY_MODE:
        return copy.deepcopy(SAMPLE_NUMVERIFY)

    url = "https://apilayer.net/api/validate"
    number_clean = e164.replace("+", "")
    params = {
        "access_key": api_key,
        "number": number_clean,
        "format": 1
    }
    r = requests.get(url, params=params, timeout=15)
    if r.status_code != 200:
        raise Exception(f"Numverify HTTP {r.status_code}: {r.text}")
    data = r.json()
    if data.get("error"):
        err_info = data.get("error", {})
        raise Exception(f"Numverify API Error: {err_info.get('info', 'Unknown')}")
    return data


# --- PARSERS (return structured data) ---
def parse_abstract(data):
    location = None
    country = None
    carrier = None
    line_type = None
    valid = None
    risk_level = None

    if "phone_number" in data:
        # Phone Intelligence nested schema
        phone_validation = data.get("phone_validation", {})
        valid = phone_validation.get("is_valid")
        phone_format = data.get("phone_format", {})
        phone_location = data.get("phone_location", {})
        location = phone_location.get("city") or phone_location.get("region")
        country = phone_location.get("country_name")
        phone_carrier = data.get("phone_carrier", {})
        carrier = phone_carrier.get("name")
        line_type = phone_carrier.get("line_type")
        risk = data.get("phone_risk", {})
        risk_level = risk.get("risk_level")
        return {
            "product": "Phone Intelligence",
            "valid": valid,
            "international": phone_format.get("international"),
            "national": phone_format.get("national"),
            "country": country,
            "location": location,
            "carrier": carrier,
            "line_type": line_type,
            "risk_level": risk_level,
            "raw": data
        }

    valid = data.get("valid", data.get("is_valid"))
    if "phone" in data:
        return {
            "product": "Phone Validation",
            "valid": valid,
            "phone": data.get("phone"),
            "country": data.get("country_name", data.get("country")),
            "location": data.get("location"),
            "carrier": data.get("carrier"),
            "line_type": data.get("type"),
            "risk_level": None,
            "raw": data
        }

    if "format" in data:
        fmt = data.get("format", {})
        country = data.get("country", {})
        return {
            "product": "Phone Validation",
            "valid": valid,
            "international": fmt.get("international"),
            "national": fmt.get("local", fmt.get("national")),
            "country": country.get("name"),
            "location": data.get("location"),
            "carrier": data.get("carrier"),
            "line_type": data.get("type"),
            "risk_level": None,
            "raw": data
        }

    return {"product": "Desconocido", "raw": data}


def parse_numverify(data):
    return {
        "valid": data.get("valid"),
        "local_format": data.get("local_format"),
        "international_format": data.get("international_format"),
        "country": data.get("country_name"),
        "location": data.get("location"),
        "carrier": data.get("carrier"),
        "line_type": data.get("line_type"),
        "raw": data
    }


def _normalize_city(city: str) -> str:
    return normalize_city(city)


def run_consensus(result: ScanResult):
    votes = []

    def add(city, source, confidence, extra=""):
        if _is_concrete_locality(str(city or "")):
            votes.append(SourceVote(str(city).strip(), source, confidence, extra))

    canonical = ""
    if result.canonical_locality_city and result.canonical_locality_state:
        canonical = f"{result.canonical_locality_city}, {result.canonical_locality_state}"
        add(canonical, result.canonical_locality_source or "IFT/LADA", 1.0)
    if result.region_phonenumbers:
        add(result.region_phonenumbers, "phonenumbers", 0.60)
    if result.abstract_location:
        add(result.abstract_location, "AbstractAPI", 0.80)
    if result.numverify_location:
        add(result.numverify_location, "NumVerify", 0.75)
    if result.ipqualityscore_data.get("city") or result.ipqualityscore_data.get("region"):
        ipqs_location = ", ".join(
            part for part in [
                result.ipqualityscore_data.get("city", ""),
                result.ipqualityscore_data.get("region", ""),
            ] if part
        )
        add(ipqs_location, "IPQualityScore", 0.65)

    decision = decide_evidence(votes)
    result.all_votes = votes
    if canonical:
        result.consensus_city = canonical
        result.consensus_confidence = 0.0
        result.consensus_sources = [result.canonical_locality_source]
        supporting = [vote for vote in votes if vote.source != result.canonical_locality_source]
        canonical_key = _locality_compare_key(canonical)
        agreeing = [vote for vote in supporting if _locality_compare_key(vote.city) == canonical_key]
        conflicting = [vote for vote in supporting if _locality_compare_key(vote.city) != canonical_key]
        if agreeing and not conflicting:
            result.evidence_state = "strong agreement"
        elif agreeing and conflicting:
            result.evidence_state = "partial agreement"
        elif conflicting:
            result.evidence_state = "conflicting sources"
        else:
            result.evidence_state = "single-source result"
    else:
        result.consensus_city = decision.city
        result.consensus_confidence = 0.0
        result.consensus_sources = decision.sources
        result.evidence_state = decision.state


# --- MAP GENERATION ---
def generate_map(result: ScanResult):
    if not result.latitude or not result.longitude:
        return ""
    try:
        import folium
        m = folium.Map(location=[result.latitude, result.longitude], zoom_start=13)
        folium.Marker(
            [result.latitude, result.longitude],
            popup=f"{result.e164}<br>{result.consensus_city}",
            tooltip="Centro aproximado de la localidad"
        ).add_to(m)
        folium.Circle(
            [result.latitude, result.longitude],
            radius=5000,
            popup="Area aproximada",
            color="red",
            fill=True,
            fill_opacity=0.1
        ).add_to(m)
        safe_num = re.sub(r"[^0-9]", "", result.e164)
        path = MAP_DIR / f"mexicosint_map_{safe_num}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        m.save(str(path))
        return str(path)
    except Exception as e:
        result.errors.append(f"Map generation: {e}")
        return ""


# --- REPORT GENERATION ---
# FIX #7: Clean report excludes internal report_path and report_hash fields
def save_report(result: ScanResult):
    try:
        safe_num = re.sub(r"[^0-9]", "", result.e164) or "unknown"
        path = REPORT_DIR / f"mexicosint_report_{safe_num}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        # Use to_report_dict() which excludes report_path and report_hash
        data = result.to_report_dict()
        data["scan_end_time"] = _now_utc()
        raw = json.dumps(data, sort_keys=True, default=str, ensure_ascii=False)
        result.report_hash = _sha256(raw)
        data["report_sha256"] = result.report_hash
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        return str(path)
    except Exception as e:
        result.errors.append(f"Report generation: {e}")
        return ""


# --- RICH PRINTERS ---
def _rich_or_plain(rich_func, plain_func):
    if RICH_AVAILABLE and sys.stdout.isatty():
        try:
            rich_func()
            return
        except Exception:
            pass
    plain_func()


def rich_print_subscriber(result: ScanResult):
    console = Console()
    table = Table(title="📋 INFORMACION DEL SUSCRIPTOR", box=box.HEAVY_EDGE,
                  title_style="bold cyan", border_style="bright_blue", show_lines=True)
    table.add_column("Campo", style="bold yellow", width=28)
    table.add_column("Valor", style="bold white", width=50)
    table.add_row("Scan ID", result.scan_id)
    table.add_row("Timestamp (UTC)", result.scan_timestamp)
    table.add_row("", "")
    table.add_row("MSISDN (E.164)", f"[bold]{result.e164}[/bold]")
    table.add_row("Valido", "[green]SI[/green]" if result.valid else "[red]NO[/red]")
    table.add_row("Region (phonenumbers)", result.region_phonenumbers or "—")
    table.add_row("Region LADA (ref.)", result.lada_region or "—")
    if result.ift_carrier:
        table.add_row("Operadora (IFT oficial)", f"[bold green]{result.ift_carrier}[/bold green]")
    if result.ift_modality:
        table.add_row("Modalidad (IFT)", result.ift_modality)
    if result.ift_fecha_asignacion:
        table.add_row("Asignado (IFT)", result.ift_fecha_asignacion)
    if result.ift_service_type:
        table.add_row("Tipo de servicio (IFT)", f"[bold red]{result.ift_service_type}[/bold red]")
    table.add_row("Operadora (Abstract)", result.abstract_carrier or "—")
    table.add_row("Operadora (NumVerify)", result.numverify_carrier or "—")
    table.add_row(
        "Tipo de linea",
        result.abstract_line_type
        if result.abstract_line_type not in ("", None, "unknown", "UNKNOWN")
        else result.numverify_line_type
        if result.numverify_line_type not in ("", None, "unknown", "UNKNOWN")
        else result.local_line_type or "—"
    )
    console.print()
    console.print(table)


def plain_print_subscriber(result: ScanResult):
    print("\n[+] INFORMACION DEL SUSCRIPTOR:")
    print("-" * 60)
    print(f"    Scan ID:             {result.scan_id}")
    print(f"    Timestamp (UTC):     {result.scan_timestamp}")
    print(f"    MSISDN (E.164):      {result.e164}")
    print(f"    Valido:              {'SI' if result.valid else 'NO'}")
    print(f"    Region (phonenumbers): {result.region_phonenumbers or '—'}")
    print(f"    Region LADA (ref.):  {result.lada_region or '—'}")
    if result.ift_carrier:
        print(f"    Operadora (IFT oficial): {result.ift_carrier}")
    if result.ift_modality:
        print(f"    Modalidad (IFT):     {result.ift_modality}")
    if result.ift_fecha_asignacion:
        print(f"    Asignado (IFT):      {result.ift_fecha_asignacion}")
    if result.ift_service_type:
        print(f"    Tipo de servicio (IFT): {result.ift_service_type}")
    print(f"    Operadora (Abstract): {result.abstract_carrier or '—'}")
    print(f"    Operadora (NumVerify): {result.numverify_carrier or '—'}")
    print(f"    Tipo de linea:       {result.abstract_line_type or result.numverify_line_type or '—'}")


def rich_print_api_results(result: ScanResult):
    console = Console()
    table = Table(title="🌐 RESULTADOS DE APIs", box=box.ROUNDED,
                  border_style="green", show_lines=True)
    table.add_column("Fuente", style="bold white", width=18)
    table.add_column("Valido", width=10)
    table.add_column("Ubicacion", style="green", width=25)
    table.add_column("Operadora", width=18)
    table.add_column("Tipo", width=12)

    if result.abstract_data:
        table.add_row(
            "AbstractAPI",
            str(result.abstract_data.get("valid", "N/A")),
            result.abstract_location or "—",
            result.abstract_carrier or "—",
            result.abstract_line_type or "—"
        )
    if result.numverify_data:
        table.add_row(
            "NumVerify",
            str(result.numverify_data.get("valid", "N/A")),
            result.numverify_location or "—",
            result.numverify_carrier or "—",
            result.numverify_line_type or "—"
        )
    if result.ipqualityscore_data:
        table.add_row(
            "IPQualityScore",
            str(result.ipqualityscore_data.get("valid", "N/A")),
            result.ipqualityscore_data.get("city") or "—",
            result.ipqualityscore_data.get("carrier") or "—",
            result.ipqualityscore_data.get("line_type") or "—",
        )
    console.print()
    console.print(table)


def plain_print_api_results(result: ScanResult):
    print("\n[+] RESULTADOS DE APIs:")
    print("-" * 60)
    if result.abstract_data:
        print(f"    [AbstractAPI] Valido: {result.abstract_data.get('valid', 'N/A')}, "
              f"Ubicacion: {result.abstract_location or '—'}, "
              f"Operadora: {result.abstract_carrier or '—'}, "
              f"Tipo: {result.abstract_line_type or '—'}")
    if result.numverify_data:
        print(f"    [NumVerify]   Valido: {result.numverify_data.get('valid', 'N/A')}, "
              f"Ubicacion: {result.numverify_location or '—'}, "
              f"Operadora: {result.numverify_carrier or '—'}, "
              f"Tipo: {result.numverify_line_type or '—'}")
    if result.ipqualityscore_data:
        print(f"    [IPQualityScore] Valido: {result.ipqualityscore_data.get('valid', 'N/A')}, "
              f"Activo: {result.ipqualityscore_data.get('active', 'N/A')}, "
              f"Riesgo: {result.ipqualityscore_data.get('risk_score', 'N/A')}, "
              f"Abuso reciente: {result.ipqualityscore_data.get('abuse_recent', 'N/A')}")


def rich_print_consensus(result: ScanResult):
    console = Console()
    if not result.all_votes:
        return
    table = Table(title="🗳️  EVIDENCIA DE LOCALIDAD", box=box.ROUNDED,
                  border_style="cyan", show_lines=True)
    table.add_column("Fuente", style="bold white", width=20)
    table.add_column("Ciudad / Region", style="green", width=30)
    for v in result.all_votes:
        table.add_row(v.source, v.city)
    table.add_row("", "")
    table.add_row("[bold green]ESTADO[/bold green]",
                  f"[bold green]{result.evidence_state}[/bold green]")
    table.add_row("[bold green]LOCALIDAD[/bold green]",
                  f"[bold green]{result.consensus_city or '—'}[/bold green]")
    console.print()
    console.print(table)


def plain_print_consensus(result: ScanResult):
    if not result.all_votes:
        return
    print("\n[+] EVIDENCIA DE LOCALIDAD:")
    print("-" * 60)
    for v in result.all_votes:
        print(f"    {v.source:18} {v.city}")
    print(f"    Estado:         {result.evidence_state}")
    print(f"    Localidad base: {result.consensus_city or '—'}")


def rich_print_geo(result: ScanResult):
    console = Console()
    table = Table(title="🗺️  GEOLOCALIZACION APROXIMADA", box=box.ROUNDED,
                  border_style="magenta", show_lines=True)
    table.add_column("Campo", style="bold yellow", width=28)
    table.add_column("Valor", style="bold white", width=50)
    table.add_row("Localidad base", result.consensus_city or "—")
    table.add_row("Latitud", f"{result.latitude:.5f}" if result.latitude else "—")
    table.add_row("Longitud", f"{result.longitude:.5f}" if result.longitude else "—")
    table.add_row("OpenCage lat/lon",
                  f"{result.opencage_latitude:.5f}, {result.opencage_longitude:.5f}"
                  if result.opencage_latitude and result.opencage_longitude else "—")
    table.add_row("OpenCage address",
                  (result.opencage_address[:70] + "...") if result.opencage_address else "—")
    table.add_row("Geoapify lat/lon",
                  f"{result.geoapify_latitude:.5f}, {result.geoapify_longitude:.5f}"
                  if result.geoapify_latitude and result.geoapify_longitude else "—")
    table.add_row("Geoapify address",
                  (result.geoapify_address[:70] + "...") if result.geoapify_address else "—")
    table.add_row("Direccion (Nominatim)", (result.nominatim_address[:70] + "...") if result.nominatim_address else "—")
    console.print()
    console.print(table)
    console.print("[dim]Nota: localidad de numeracion; NO GPS en tiempo real ni ubicacion del suscriptor.[/dim]")


def plain_print_geo(result: ScanResult):
    print("\n[+] GEOLOCALIZACION APROXIMADA:")
    print("-" * 60)
    print(f"    Localidad base:  {result.consensus_city or '—'}")
    print(f"    Latitud:         {result.latitude:.5f}" if result.latitude else "    Latitud:         —")
    print(f"    Longitud:        {result.longitude:.5f}" if result.longitude else "    Longitud:        —")
    if result.opencage_latitude and result.opencage_longitude:
        print(f"    OpenCage lat/lon: {result.opencage_latitude:.5f}, {result.opencage_longitude:.5f}")
    if result.opencage_address:
        print(f"    OpenCage address: {result.opencage_address[:70]}")
    if result.geoapify_latitude and result.geoapify_longitude:
        print(f"    Geoapify lat/lon: {result.geoapify_latitude:.5f}, {result.geoapify_longitude:.5f}")
    if result.geoapify_address:
        print(f"    Geoapify address: {result.geoapify_address[:70]}")
    if result.nominatim_address:
        print(f"    Direccion (Nominatim): {result.nominatim_address[:70]}")
    print("    Nota: localidad de numeracion; NO GPS en tiempo real ni ubicacion del suscriptor.")


def rich_print_osint_links(links: dict):
    console = Console()
    table = Table(title="🔗 ENLACES DE INVESTIGACION (OSINT)", box=box.ROUNDED,
                  border_style="blue", show_lines=True)
    table.add_column("Plataforma", style="bold white", width=22)
    table.add_column("URL", style="cyan")
    for name, url in links.items():
        table.add_row(name, url)
    console.print()
    console.print(table)


def plain_print_osint_links(links: dict):
    print("\n[+] ENLACES DE INVESTIGACION (OSINT):")
    print("-" * 60)
    for name, url in links.items():
        print(f"    {name:22} {url}")


def rich_print_report(result: ScanResult):
    console = Console()
    table = Table(title="📁 REPORTE EXPORTADO", box=box.ROUNDED,
                  border_style="yellow", show_lines=True)
    table.add_column("Campo", style="bold yellow", width=28)
    table.add_column("Valor", style="bold white", width=50)
    table.add_row("Reporte JSON", result.report_path or "—")
    table.add_row("Mapa HTML", result.map_path or "—")
    table.add_row("Hash SHA-256", result.report_hash or "—")
    console.print()
    console.print(table)


def plain_print_report(result: ScanResult):
    print("\n[+] REPORTE EXPORTADO:")
    print("-" * 60)
    print(f"    Reporte JSON: {result.report_path or '—'}")
    print(f"    Mapa HTML:    {result.map_path or '—'}")
    print(f"    Hash SHA-256: {result.report_hash or '—'}")


# --- OSINT LINKS ---
# FIX #9: Only include links that genuinely perform phone number lookups
def generate_osint_links(e164):
    num_no_plus = e164.replace("+", "")
    num10 = num_no_plus[2:]
    spaced = f"+52 {num10[:3]} {num10[3:6]} {num10[6:]}" if len(num10) == 10 else e164

    def google(query: str) -> str:
        return f"https://www.google.com/search?q={urllib.parse.quote(query)}"

    links = {
        "WhatsApp (wa.me)": f"https://wa.me/{num_no_plus}",
        "Google exact E.164": google(f'"{e164}"'),
        "Google exact international": google(f'"{num_no_plus}"'),
        "Google exact national": google(f'"{num10}"'),
        "Google exact spaced": google(f'"{spaced}"'),
        "Google site:facebook.com": google(f'site:facebook.com "{num_no_plus}" OR "{num10}"'),
        "Google site:tiktok.com": google(f'site:tiktok.com "{num_no_plus}" OR "{num10}"'),
        "Google site:x.com": google(f'site:x.com "{num_no_plus}" OR "{num10}"'),
        "Google site:twitter.com": google(f'site:twitter.com "{num_no_plus}" OR "{num10}"'),
        "Formato E.164": e164,
    }
    return links


# --- MAIN ---
def run_phone_scan(raw: str, config: dict, active: list) -> ScanResult:
    result = ScanResult()
    result.scan_id = f"MX-{uuid.uuid4().hex[:10].upper()}"
    result.raw_input = raw

    normalized = normalize_mx_number(raw)
    result.detected_format = normalized.detected_format
    result.international_digits = normalized.international_digits
    result.is_possible = normalized.is_possible
    result.is_mexican = normalized.is_mexican

    validated = validate_mx_number(raw)
    if not validated:
        sys.exit(1)

    e164, parsed = validated
    result.e164 = e164
    result.valid = True
    result.country_code = f"+{parsed.country_code}"
    result.national_number = str(parsed.national_number)

    local_info = parse_mx_number(raw)
    result.region_phonenumbers = geocode_phonenumbers(parsed)
    result.lada_region = detect_lada_region(result.national_number)
    if not result.lada_region and local_info.get("city") != "Unknown" and local_info.get("state") != "Unknown":
        result.lada_region = f"{local_info.get('city')}, {local_info.get('state')}"
    has_ift_block = False
    if IFT_BLOCKS_AVAILABLE:
        try:
            block = lookup_block(result.national_number)
            if block:
                has_ift_block = True
                result.ift_carrier = block.get("carrier", "")
                result.ift_modality = modality_label(block.get("modality", ""))
                result.ift_zona = block.get("zona", "")
                result.ift_fecha_asignacion = block.get("fecha_asignacion", "")
                result.ift_service_type = block.get("service_type", "")
        except Exception as e:
            result.errors.append(f"ift_blocks: {e}")
    _set_canonical_locality(result, local_info, has_ift_block)
    result.local_line_type = (
        "CELULAR PROBABLE"
        if local_info.get("is_mobile")
        else "LÍNEA FIJA"
        if local_info.get("number_type") == "FIXED_LINE"
        else ""
    )
    result.osint_links = generate_osint_links(e164)

    # API calls
    api_results = {}

    if "abstract_phone_intelligence" in active:
        try:
            _trace_provider(result, "AbstractAPI", "fixture" if DUMMY_MODE else "live_request", normalized)
            api_results["abstract_intel"] = abstract_phone_intelligence_lookup(
                e164, _get_api_key(config, "abstract_phone_intelligence")
            )
        except Exception as e:
            api_results["abstract_intel"] = None
            result.errors.append(f"abstract_intel: {e}")
            _trace_provider(result, "AbstractAPI", "error", normalized, note=type(e).__name__)
    else:
        _trace_provider(result, "AbstractAPI", "skipped", normalized)

    if "numverify" in active:
        try:
            _trace_provider(result, "NumVerify", "fixture" if DUMMY_MODE else "live_request", normalized)
            api_results["numverify"] = numverify_lookup(e164, _get_api_key(config, "numverify"))
        except Exception as e:
            api_results["numverify"] = None
            result.errors.append(f"numverify: {e}")
            _trace_provider(result, "NumVerify", "error", normalized, note=type(e).__name__)
    else:
        _trace_provider(result, "NumVerify", "skipped", normalized)

    if "ipqualityscore" in active:
        try:
            if DUMMY_MODE:
                _trace_provider(result, "IPQualityScore", "fixture", normalized)
                result.ipqualityscore_data = copy.deepcopy(SAMPLE_IPQUALITYSCORE)
            else:
                _trace_provider(result, "IPQualityScore", "live_request", normalized)
                reputation = IPQualityScoreProvider(_get_api_key(config, "ipqualityscore")).lookup(normalized)
                if reputation:
                    result.ipqualityscore_data = asdict(reputation)
        except Exception as e:
            result.errors.append(f"ipqualityscore: {e}")
            _trace_provider(result, "IPQualityScore", "error", normalized, note=type(e).__name__)
    else:
        _trace_provider(result, "IPQualityScore", "skipped", normalized)

    # Process Abstract Phone Intelligence results
    if "abstract_intel" in api_results and api_results["abstract_intel"]:
        parsed_abs = parse_abstract(api_results["abstract_intel"])
        result.abstract_data = parsed_abs
        result.abstract_location = parsed_abs.get("location")
        result.abstract_carrier = parsed_abs.get("carrier")
        result.abstract_line_type = parsed_abs.get("line_type")

    if "numverify" in api_results and api_results["numverify"]:
        parsed_nv = parse_numverify(api_results["numverify"])
        result.numverify_data = parsed_nv
        result.numverify_location = parsed_nv.get("location")
        result.numverify_carrier = parsed_nv.get("carrier")
        result.numverify_line_type = parsed_nv.get("line_type")

    # Consensus
    run_consensus(result)

    # Geocode only canonical concrete city/state locality.
    geo_target = result.canonical_locality_query

    if not _is_concrete_locality(geo_target):
        _trace_provider(result, "OpenCage", "skipped", normalized, locality_query=geo_target or "", note="no_concrete_locality")
        _trace_provider(result, "Geoapify", "skipped", normalized, locality_query=geo_target or "", note="no_concrete_locality")
        _trace_provider(result, "Nominatim", "skipped", normalized, locality_query=geo_target or "", note="no_concrete_locality")
    elif geo_target:
        if DUMMY_MODE:
            print("\n[*] Geocodificando localidad...")
            print("    [!] Omitido en modo dummy para evitar llamadas de red.")
            _trace_provider(result, "OpenCage", "fixture", normalized, locality_query=geo_target)
            _trace_provider(result, "Geoapify", "fixture", normalized, locality_query=geo_target)
            result.geoapify_data = copy.deepcopy(SAMPLE_GEOAPIFY)
        else:
            print("\n[*] Geocodificando localidad de numeracion (OpenCage primario, Geoapify respaldo, Nominatim final)...")
            if "opencage" in active:
                try:
                    locality, status = _lookup_cached_geocoder(
                        OpenCageProvider(_get_api_key(config, "opencage")),
                        geo_target,
                    )
                    _trace_provider(result, "OpenCage", status, normalized, locality_query=geo_target)
                    if locality:
                        result.opencage_data = asdict(locality)
                        result.opencage_latitude = locality.latitude
                        result.opencage_longitude = locality.longitude
                        result.opencage_address = locality.formatted_address
                except Exception as e:
                    result.errors.append(f"opencage: {e}")
                    _trace_provider(result, "OpenCage", "error", normalized, locality_query=geo_target, note=type(e).__name__)
            else:
                _trace_provider(result, "OpenCage", "skipped", normalized, locality_query=geo_target)

            if result.opencage_latitude and result.opencage_longitude:
                result.latitude, result.longitude = result.opencage_latitude, result.opencage_longitude
                print("    [OpenCage] OK")
                _trace_provider(result, "Geoapify", "skipped", normalized, locality_query=geo_target, note="opencage_result")
            elif "geoapify" in active:
                try:
                    locality, status = _lookup_cached_geocoder(
                        GeoapifyProvider(_get_api_key(config, "geoapify")),
                        geo_target,
                    )
                    _trace_provider(result, "Geoapify", status, normalized, locality_query=geo_target)
                    if locality:
                        result.geoapify_data = asdict(locality)
                        result.geoapify_latitude = locality.latitude
                        result.geoapify_longitude = locality.longitude
                        result.geoapify_address = locality.formatted_address
                except Exception as e:
                    result.errors.append(f"geoapify: {e}")
                    _trace_provider(result, "Geoapify", "error", normalized, locality_query=geo_target, note=type(e).__name__)
            else:
                _trace_provider(result, "Geoapify", "skipped", normalized, locality_query=geo_target)

            if result.geoapify_latitude and result.geoapify_longitude:
                result.latitude, result.longitude = result.geoapify_latitude, result.geoapify_longitude
                print("    [Geoapify] OK")
            elif not result.latitude or not result.longitude:
                print("    [OpenCage/Geoapify] Sin key/resultado, usando Nominatim...")
                _trace_provider(result, "Nominatim", "live_request", normalized, locality_query=geo_target)
                result.latitude, result.longitude, result.nominatim_address = geocode_nominatim(geo_target)
            else:
                _trace_provider(result, "Nominatim", "skipped", normalized, locality_query=geo_target)

    # Map
    if result.latitude and result.longitude:
        result.map_path = generate_map(result)

    # Report
    result.report_path = save_report(result)

    return result


def print_results(result: ScanResult):
    _rich_or_plain(
        lambda: rich_print_subscriber(result),
        lambda: plain_print_subscriber(result)
    )
    _rich_or_plain(
        lambda: rich_print_osint_links(result.osint_links),
        lambda: plain_print_osint_links(result.osint_links)
    )
    _rich_or_plain(
        lambda: rich_print_api_results(result),
        lambda: plain_print_api_results(result)
    )
    _rich_or_plain(
        lambda: rich_print_consensus(result),
        lambda: plain_print_consensus(result)
    )
    if result.consensus_city:
        _rich_or_plain(
            lambda: rich_print_geo(result),
            lambda: plain_print_geo(result)
        )
    _rich_or_plain(
        lambda: rich_print_report(result),
        lambda: plain_print_report(result)
    )

    # FIX #5: Correct portability dates - implemented 2008, 10-digit dialing 2019
    print("\n[!] ADVERTENCIA: La portabilidad numerica en Mexico se implemento en 2008.")
    print("    El cambio a marcado de 10 digitos (sin 01, 044, 045) ocurrio en 2019.")
    print("    El numero pudo haber sido portado a otra operadora o region.")
    print("    La ubicacion mostrada es la del prefijo original/consenso de APIs,")
    print("    NO garantiza la posicion exacta/GPS del telefono.")


def main(argv=None):
    global DUMMY_MODE, SMALL_BANNER

    args = list(sys.argv[1:] if argv is None else argv)
    DUMMY_MODE = False
    SMALL_BANNER = False

    if "--dummy-test" in args:
        DUMMY_MODE = True
        args.remove("--dummy-test")
        print("\n[!] MODO DUMMY ACTIVADO: No se realizaran llamadas reales a las APIs.")
        print("    Se usaran datos de ejemplo. No se consumiran creditos.\n")

    banner_flags = {"-b", "--compact-banner", "--small-banner"}
    if any(flag in args for flag in banner_flags):
        SMALL_BANNER = True
        args = [arg for arg in args if arg not in banner_flags]

    print_banner()

    number = args[0] if args else None

    if not number:
        print("Uso: mexicosint <numero_mexicano>")
        print("     mexicosint --dummy-test <numero_mexicano>")
        print("Ejemplos:")
        print("    mexicosint 5512345678")
        print("    mexicosint +525512345678")
        print("    mexicosint --set-key geoapify TU_KEY")
        print("    mexicosint --list-keys")
        sys.exit(1)

    print(f"[+] Fecha/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    config = init_config()
    active = check_keys(config)

    if number:
        print(f"[+] Entrada cruda: {number}")
        print("=" * 60)
        result = run_phone_scan(number, config, active)
        print_results(result)

    print("\n[*] Escaneo completado.")
    print("=" * 60)


if __name__ == "__main__":
    main()
