"""IFT numbering-block lookup (Plan Nacional de Numeracion).

Offline lookup of official IFT block assignments:
which carrier owns which number ranges, mobile/fixed modality,
plus non-geographic series (200/300/500/800/900) service types.

Data: sns.ift.org.mx (Sistema de Numeracion y Senalizacion, descarga publica).
"""

from __future__ import annotations

import bisect
import csv
import gzip
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
BLOCKS_FILE = DATA_DIR / "ift_blocks.csv.gz"
NG_FILE = DATA_DIR / "ift_ng_blocks.csv.gz"

NG_SERVICE_TYPES = {
    "200": "Telefonia satelital (pago en el origen)",
    "300": "Cobro compartido",
    "500": "Numeros personales (transferencia de llamadas)",
    "800": "Numero no geografico - cobro revertido (toll-free)",
    "900": "Numero no geografico - sobre cuota (PREMIUM, posible estafa)",
}

_blocks_cache: list | None = None
_starts_cache: list | None = None
_ng_cache: dict | None = None


def _load_blocks() -> tuple[list, list]:
    """Load (rows, starts) for binary search. Rows: (end, carrier, modality, zone, fecha)."""
    global _blocks_cache, _starts_cache
    if _blocks_cache is None:
        rows = []
        starts = []
        if BLOCKS_FILE.exists():
            with gzip.open(BLOCKS_FILE, "rt", encoding="utf-8") as f:
                for r in csv.reader(f):
                    if len(r) < 6:
                        continue
                    ini, fin, carrier, modality, zona, fecha = r[:6]
                    starts.append(int(ini))
                    rows.append((int(fin), carrier, modality, zona, fecha))
        _starts_cache = starts
        _blocks_cache = rows
    return _blocks_cache, _starts_cache


def _load_ng() -> dict:
    """Load non-geographic blocks: {(cve, serie): (pst, ini, fin)}."""
    global _ng_cache
    if _ng_cache is None:
        ng = {}
        if NG_FILE.exists():
            with gzip.open(NG_FILE, "rt", encoding="utf-8") as f:
                for r in csv.reader(f):
                    if len(r) < 5:
                        continue
                    cve, serie, ini, fin, pst = r[:5]
                    ng[(cve, serie)] = (pst, ini, fin)
        _ng_cache = ng
    return _ng_cache


def lookup_block(national_number: str) -> dict:
    """Look up a 10-digit Mexican national number in the IFT block registry.

    Returns dict with carrier, modality, zona, fecha_asignacion, service_type,
    source='IFT/PNN'. Empty dict if not found or data missing.
    """
    num = "".join(c for c in national_number if c.isdigit())
    if len(num) == 11 and num.startswith("1"):
        num = num[1:]
    if len(num) != 10:
        return {}

    ng = lookup_non_geographic(num)
    if ng:
        return ng

    rows, starts = _load_blocks()
    if not rows:
        return {}
    n = int(num)
    # find rightmost block with start <= n
    i = bisect.bisect_right(starts, n) - 1
    if i >= 0:
        fin, carrier, modality, zona, fecha = rows[i]
        if n <= fin:
            return {
                "carrier": carrier,
                "modality": modality,
                "zona": zona,
                "fecha_asignacion": fecha,
                "service_type": "",
                "source": "IFT/PNN",
            }
    return {}


def lookup_non_geographic(national_number: str) -> dict:
    """Check 200/300/500/800/900 series. Returns block info or {}."""
    num = national_number
    if len(num) < 6:
        return {}
    cve = num[:3]
    if cve not in NG_SERVICE_TYPES:
        return {}
    serie = num[3:6]
    tail = num[6:10].ljust(4, "0")
    ng = _load_ng()
    entry = ng.get((cve, serie))
    if not entry:
        return {"service_type": NG_SERVICE_TYPES[cve], "carrier": "", "modality": "NO-GEO",
                "zona": "", "fecha_asignacion": "", "source": "IFT/PNN"}
    pst, ini, fin = entry
    if ini <= tail <= fin:
        return {
            "carrier": pst,
            "modality": "NO-GEO",
            "zona": "",
            "fecha_asignacion": "",
            "service_type": NG_SERVICE_TYPES[cve],
            "source": "IFT/PNN",
        }
    return {}


def modality_label(mod: str) -> str:
    return {
        "FIJO": "Linea fija",
        "CPP": "Movil (CPP)",
        "MPP": "Movil (MPP)",
        "NO-GEO": "No geografico",
    }.get(mod, mod)
