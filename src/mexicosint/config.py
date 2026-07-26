"""Runtime config and API-key management."""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path

CONFIG_PATH = Path.home() / ".mx_osint_config.json"

SAMPLE_CONFIG = {
    "abstract_phone_intelligence": "",
    "numverify": "",
    "opencage": "",
    "geoapify": "",
    "google_places": "",
    "ipqualityscore": "",
}

SERVICE_ALIASES = {
    "abstract": "abstract_phone_intelligence",
}


def canonical_service(name: str) -> str:
    return SERVICE_ALIASES.get(name.strip().lower(), name.strip().lower())


def mask_key(value: str) -> str:
    if not isinstance(value, str) or len(value) <= 5:
        return "FALTANTE"
    return f"{value[:4]}{'*' * 8} (guardada, {len(value)} caracteres)"


def init_config(config_path: Path = CONFIG_PATH, dummy_mode: bool = False) -> dict:
    if dummy_mode:
        print("[*] Modo dummy: usando configuracion de prueba en memoria.")
        return {k: f"dummy_key_{k}" for k in SAMPLE_CONFIG}

    if not config_path.exists():
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(SAMPLE_CONFIG, f, indent=2, ensure_ascii=False)
        os.chmod(config_path, stat.S_IRUSR | stat.S_IWUSR)
        print(f"[!] Archivo de configuracion creado: {config_path}")
        print("[!] Editalo y agrega tus API keys, luego ejecuta de nuevo.")
        raise SystemExit(0)

    config_stat = config_path.stat()
    current_mode = config_stat.st_mode & 0o777
    if current_mode != 0o600:
        print(f"[!] ADVERTENCIA: Permisos del config son {oct(current_mode)}, deberian ser 0o600.")
        print(f"    Ejecuta: chmod 600 {config_path}")

    with open(config_path, encoding="utf-8") as f:
        return json.load(f)


def check_keys(config: dict, dummy_mode: bool = False) -> list[str]:
    print("\n[*] Estado de API Keys:")
    active = []
    canonical_config = {}
    for key, value in config.items():
        canonical = canonical_service(key)
        canonical_config.setdefault(canonical, value)

    for key, value in canonical_config.items():
        if dummy_mode:
            print(f"    {key:30} OK (dummy)")
            active.append(key)
        elif isinstance(value, str) and len(value) > 5:
            print(f"    {key:30} OK (presente)")
            active.append(key)
        else:
            print(f"    {key:30} FALTANTE")
    if not dummy_mode:
        print("[!] Nota: 'OK' solo indica que la key no esta vacia.")
        print("    No se valido contra la API para no consumir creditos.")
    return active


def get_api_key(config: dict, key: str) -> str:
    if config.get(key):
        return config[key]
    legacy = {alias: canonical for alias, canonical in SERVICE_ALIASES.items() if canonical == key}
    for alias in legacy:
        if config.get(alias):
            return config[alias]
    return ""


def set_key(service: str, key: str, config_path: Path = CONFIG_PATH) -> int:
    canonical = canonical_service(service)
    if canonical not in SAMPLE_CONFIG:
        print(f"[!] Servicio desconocido: '{service}'")
        print(f"    Servicios validos: {', '.join(SAMPLE_CONFIG)}")
        aliases = ", ".join(f"{a} -> {c}" for a, c in SERVICE_ALIASES.items())
        print(f"    Alias: {aliases}")
        return 1

    if config_path.exists():
        try:
            with open(config_path, encoding="utf-8") as f:
                config = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"[!] No se pudo leer {config_path}: {e}")
            return 1
    else:
        config = dict(SAMPLE_CONFIG)

    config[canonical] = key.strip()
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    os.chmod(config_path, stat.S_IRUSR | stat.S_IWUSR)
    print(f"[+] Key guardada para '{canonical}' en {config_path}")
    print("    Permisos: 0o600 (solo tu usuario puede leerla).")
    return 0


def list_keys(config_path: Path = CONFIG_PATH) -> int:
    print(f"[*] Archivo de configuracion: {config_path}")
    if not config_path.exists():
        print("    No existe todavia. Usa --set-key para crear la primera key.")
        return 0
    try:
        with open(config_path, encoding="utf-8") as f:
            config = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"[!] No se pudo leer el config: {e}")
        return 1
    print("[*] Estado de API Keys:")
    for service in SAMPLE_CONFIG:
        print(f"    {service:30} {mask_key(config.get(service, ''))}")
    extra = [key for key in config if key not in SAMPLE_CONFIG]
    for service in extra:
        print(f"    {service:30} {mask_key(config.get(service, ''))} (extra)")
    return 0
