"""Locality normalization and vague-location filtering."""

from __future__ import annotations

import re
import unicodedata
from functools import lru_cache

VAGUE_LOCATIONS = {
    "unknown",
    "mexico",
    "méxico",
    "unknown city",
    "n/a",
    "not found",
    "sin informacion",
    "no hay informacion",
    "desconocido",
    "indefinido",
    "general",
    "nacional",
    "republica mexicana",
    "estados unidos mexicanos",
}

GENERIC_LOCALITIES = {
    "northwest",
    "north west",
    "noroeste",
    "noroeste de mexico",
    "northeast",
    "north east",
    "noreste",
    "noreste de mexico",
    "central",
    "centro",
    "sur",
    "south",
    "southeast",
    "south east",
    "sureste",
    "southwest",
    "south west",
    "suroeste",
    "baja california",
    "baja california sur",
    "sonora",
    "chihuahua",
    "coahuila",
    "nuevo leon",
    "tamaulipas",
    "sinaloa",
    "durango",
    "zacatecas",
    "jalisco",
    "colima",
    "michoacan",
    "guanajuato",
    "queretaro",
    "hidalgo",
    "estado de mexico",
    "morelos",
    "puebla",
    "tlaxcala",
    "veracruz",
    "guerrero",
    "oaxaca",
    "chiapas",
    "tabasco",
    "campeche",
    "yucatan",
    "quintana roo",
    "aguascalientes",
    "nayarit",
    "san luis potosi",
}

_NON_ALNUM_COMMA_RE = re.compile(r"[^a-z0-9\s,]")
_WHITESPACE_RE = re.compile(r"\s+")


@lru_cache(maxsize=1024)
def normalize_for_vague(city_region: str) -> str:
    normalized = city_region.lower().strip()
    return unicodedata.normalize("NFKD", normalized).encode(
        "ASCII", "ignore"
    ).decode("ASCII")


@lru_cache(maxsize=1024)
def is_concrete_locality(city_region: str) -> bool:
    if not city_region:
        return False
    normalized = normalize_for_vague(city_region)
    normalized = _NON_ALNUM_COMMA_RE.sub(" ", normalized)
    normalized = _WHITESPACE_RE.sub(" ", normalized).strip()
    compact = normalized.replace(",", " ").strip()
    if not compact:
        return False
    if compact in VAGUE_LOCATIONS or compact in GENERIC_LOCALITIES:
        return False
    return any(char.isalpha() for char in compact) and len(compact) >= 3


def clean_place_name(value: str) -> str:
    value = (value or "").strip()
    if not value or value.lower() == "unknown":
        return ""
    value = unicodedata.normalize("NFKD", value).encode(
        "ASCII", "ignore"
    ).decode("ASCII")
    aliases = {
        "CDMX": "Ciudad de Mexico",
        "Distrito Federal": "Ciudad de Mexico",
        "Mexico City": "Ciudad de Mexico",
    }
    return aliases.get(value, value)


def split_lada_region(region: str) -> tuple[str, str]:
    if not region or "," not in region:
        return "", ""
    city, state = [part.strip() for part in region.split(",", 1)]
    return clean_place_name(city), clean_place_name(state)
