#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
update_ift_blocks.py - Descarga y normaliza las bases de numeracion del IFT.

Fuentes (sns.ift.org.mx, JSF/PrimeFaces):
  - Plan Nacional de Numeracion (publico):
    https://sns.ift.org.mx/sns-frontend/planes-numeracion/descarga-publica.xhtml
    (form FORM_planes, boton FORM_planes:BTN_planPublico1; la respuesta es un
    ZIP con un unico CSV)
  - Numeracion no geografica (series 200/300/500/800/900):
    https://sns.ift.org.mx/sns-frontend/descarga-numeracion-no-geografica/descarga-numeracion-no-geografica.xhtml
    (form FORM_DesNoGeo, botones FORM_DesNoGeo:TBL_descargaNNG:0..4:j_idt52)

Los CSV crudos se guardan en src/mexicosint/data/raw_pnn/ y se normalizan a:
  - src/mexicosint/data/ift_blocks.csv.gz    (ini,fin,carrier,modalidad,zona,fecha)
  - src/mexicosint/data/ift_ng_blocks.csv.gz (cve,serie,ini,fin,carrier)

Uso:
    python3 tools/update_ift_blocks.py            # descarga + normaliza
    python3 tools/update_ift_blocks.py --offline  # solo normaliza desde raw_pnn/
"""

import csv
import gzip
import io
import re
import sys
import zipfile
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "src" / "mexicosint" / "data"
RAW_DIR = DATA_DIR / "raw_pnn"
BLOCKS_OUT = DATA_DIR / "ift_blocks.csv.gz"
NG_OUT = DATA_DIR / "ift_ng_blocks.csv.gz"

PNN_URL = "https://sns.ift.org.mx/sns-frontend/planes-numeracion/descarga-publica.xhtml"
NNG_URL = "https://sns.ift.org.mx/sns-frontend/descarga-numeracion-no-geografica/descarga-numeracion-no-geografica.xhtml"

# Serie no geografica -> indice de fila en TBL_descargaNNG
NG_SERIES = {"200": 0, "300": 1, "500": 2, "800": 3, "900": 4}

# Razon social -> marca comercial
BRAND_MAP = {
    "RADIOMOVIL DIPSA": "Telcel",
    "TELEFONOS DE MEXICO": "Telmex",
    "AT&T COMERCIALIZACION MOVIL": "AT&T",
    "PEGASO PCS": "Movistar",
}

VIEWSTATE_RE = re.compile(
    r'name="javax\.faces\.ViewState"[^>]*value="([^"]+)"'
    r'|value="([^"]+)"[^>]*name="javax\.faces\.ViewState"'
)

TIMEOUT = 120


def extract_viewstate(html: str) -> str:
    m = VIEWSTATE_RE.search(html)
    if not m:
        raise RuntimeError("No se encontro javax.faces.ViewState en la pagina")
    return m.group(1) or m.group(2)


def jsf_post(session: requests.Session, url: str, form: str, button: str) -> bytes:
    """Simula el POST JSF: GET para ViewState, luego POST con el boton."""
    r = session.get(url, timeout=TIMEOUT)
    r.raise_for_status()
    payload = {
        form: form,
        button: button,
        "javax.faces.ViewState": extract_viewstate(r.text),
    }
    r = session.post(url, data=payload, timeout=TIMEOUT)
    r.raise_for_status()
    return r.content


def save_csvs(blob: bytes, prefix: str) -> list:
    """Guarda el/los CSV de una respuesta (ZIP o CSV directo) en raw_pnn/."""
    saved = []
    if blob[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(blob)) as zf:
            for name in zf.namelist():
                if name.lower().endswith(".csv"):
                    dest = RAW_DIR / Path(name).name
                    dest.write_bytes(zf.read(name))
                    saved.append(dest)
    else:
        dest = RAW_DIR / f"{prefix}.csv"
        dest.write_bytes(blob)
        saved.append(dest)
    return saved


def download() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update({"User-Agent": "MeXicOSINT/2.5.0 (OSINT research)"})

    print("[*] Descargando Plan Nacional de Numeracion (publico)...")
    for p in save_csvs(
        jsf_post(session, PNN_URL, "FORM_planes", "FORM_planes:BTN_planPublico1"),
        "pnn_publico",
    ):
        print(f"    -> {p.name}")

    for serie, idx in NG_SERIES.items():
        print(f"[*] Descargando numeracion no geografica serie {serie}...")
        for p in save_csvs(
            jsf_post(session, NNG_URL, "FORM_DesNoGeo",
                     f"FORM_DesNoGeo:TBL_descargaNNG:{idx}:j_idt52"),
            f"nng_{serie}",
        ):
            print(f"    -> {p.name}")


def normalize_carrier(razon_social: str) -> str:
    rs = " ".join(razon_social.split()).strip().strip('"')
    up = rs.upper()
    for key, brand in BRAND_MAP.items():
        if key in up:
            return brand
    return rs.title() if rs else ""


def read_rows(path: Path) -> tuple:
    """Devuelve (headers_upper, filas) soportando latin-1 y utf-8."""
    for enc in ("utf-8-sig", "latin-1"):
        try:
            with open(path, encoding=enc, newline="") as f:
                rows = [r for r in csv.reader(f) if any(c.strip() for c in r)]
            return [h.strip().upper() for h in rows[0]], rows[1:]
        except UnicodeDecodeError:
            continue
    raise RuntimeError(f"No se pudo decodificar {path}")


def col(headers: list, *keywords: str) -> int:
    for kw in keywords:
        for i, h in enumerate(headers):
            if kw in h:
                return i
    raise RuntimeError(f"Columna {keywords} no encontrada en {headers}")


def normalize() -> None:
    geo, ng = [], []
    for path in sorted(RAW_DIR.glob("*.csv")):
        headers, rows = read_rows(path)
        if "NUMERACION" in " ".join(headers) and any("ZONA" in h for h in headers):
            i_ini = col(headers, "INICIAL")
            i_fin = col(headers, "FINAL")
            i_pst = col(headers, "RAZON", "CONCESIONARIO", "PRESTADOR")
            i_mod = col(headers, "MODALIDAD")
            i_zona = col(headers, "ZONA")
            i_fecha = col(headers, "FECHA")
            for r in rows:
                if len(r) <= max(i_ini, i_fin, i_pst, i_mod, i_zona, i_fecha):
                    continue
                ini, fin = r[i_ini].strip(), r[i_fin].strip()
                if not (ini.isdigit() and fin.isdigit()):
                    continue
                geo.append((ini, fin, normalize_carrier(r[i_pst]),
                            r[i_mod].strip(), r[i_zona].strip(), r[i_fecha].strip()))
        elif any("SERIE" in h for h in headers):
            i_cve = col(headers, "CLAVE", "SERVICIO")
            i_serie = col(headers, "SERIE")
            i_ini = col(headers, "INICIAL")
            i_fin = col(headers, "FINAL")
            i_pst = col(headers, "PST", "RAZON", "CONCESIONARIO", "PRESTADOR")
            for r in rows:
                if len(r) <= max(i_cve, i_serie, i_ini, i_fin, i_pst):
                    continue
                ng.append((r[i_cve].strip(), r[i_serie].strip(),
                           r[i_ini].strip(), r[i_fin].strip(),
                           normalize_carrier(r[i_pst])))

    if not geo:
        raise RuntimeError("No se encontraron bloques geograficos en raw_pnn/")

    geo.sort(key=lambda r: int(r[0]))
    ng.sort(key=lambda r: (r[0], r[1], r[2]))

    with gzip.open(BLOCKS_OUT, "wt", encoding="utf-8", newline="") as f:
        csv.writer(f).writerows(geo)
    print(f"[+] {BLOCKS_OUT.name}: {len(geo)} bloques")

    with gzip.open(NG_OUT, "wt", encoding="utf-8", newline="") as f:
        csv.writer(f).writerows(ng)
    print(f"[+] {NG_OUT.name}: {len(ng)} bloques no geograficos")


def main() -> None:
    offline = "--offline" in sys.argv
    if not offline:
        download()
    normalize()


if __name__ == "__main__":
    main()
