"""Runtime config and API-key management.

Key resolution order per service:
  1. Environment variable  (MEXICOSINT_<SERVICE>_API_KEY or custom mapping)
  2. MicroVault            (encrypted vault at ~/.microvault/vault.enc)
  3. JSON config file      (plaintext fallback at ~/.mx_osint_config.json)

The JSON file is entirely optional. If all your keys live in MicroVault
or env vars, MeXiCOSINT will never touch the JSON file.
"""

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
    "ipqualityscore": "",
}

SERVICE_ALIASES = {
    "abstract": "abstract_phone_intelligence",
}

# ── Environment variable mappings ──────────────────────────────────────
# Highest priority source.  Checked before MicroVault and JSON config.
# Each service maps to a list of env-var names, checked in order:
#   [0] MeXiCOSINT's own prefixed name (MEXICOSINT_*)
#   [1] MicroVault's default export name (<SERVICE>_API_KEY) — so
#       `eval "$(microvault env)"` works directly, no alias needed.
ENV_VAR_MAP = {
    "abstract_phone_intelligence": [
        "MEXICOSINT_ABSTRACT_API_KEY",
        "ABSTRACT_PHONE_INTELLIGENCE_API_KEY",
        "ABSTRACT_API_KEY",
    ],
    "numverify": [
        "MEXICOSINT_NUMVERIFY_API_KEY",
        "NUMVERIFY_API_KEY",
    ],
    "opencage": [
        "MEXICOSINT_OPENCAGE_API_KEY",
        "OPENCAGE_API_KEY",
    ],
    "geoapify": [
        "MEXICOSINT_GEOAPIFY_API_KEY",
        "GEOAPIFY_API_KEY",
    ],
    "ipqualityscore": [
        "MEXICOSINT_IPQS_API_KEY",
        "IPQUALITYSCORE_API_KEY",
        "IPGS_API_KEY",
    ],
}


def _env_var_names(service: str) -> list[str]:
    return ENV_VAR_MAP.get(service, [])


def _from_env(service: str) -> str:
    for name in _env_var_names(service):
        val = os.environ.get(name, "").strip()
        if val:
            return val
    return ""


# ── MicroVault service-name mappings ───────────────────────────────────
# Maps MeXiCOSINT service names to the names actually stored in MicroVault.
# (The user's vault uses a *_api suffix convention; geoapify and ipgs are
# stored without it.) Customize here rather than renaming vault entries,
# since the same vault entries are shared by other tools.
MICROVAULT_SERVICES = {
    "abstract_phone_intelligence": "abstract_api",
    "numverify":                   "numverify_api",
    "opencage":                    "opencage_api",
    "geoapify":                    "geoapify",
    "ipqualityscore":              "ipgs",
}

# Lazy-loaded MicroVault bridge
_mv_bridge = None


def _get_microvault_bridge():
    """Try to connect to MicroVault via the bridge. Returns bridge or None."""
    global _mv_bridge
    if _mv_bridge is not None:
        return _mv_bridge if _mv_bridge._available else None
    from mexicosint.microvault_bridge import get_bridge
    _mv_bridge = get_bridge()
    if _mv_bridge.is_available():
        return _mv_bridge
    return None


def _get_from_microvault(service: str) -> str:
    """Look up a single key from MicroVault. Returns '' if unavailable."""
    bridge = _get_microvault_bridge()
    if bridge is None:
        return ""
    if not bridge._connected:
        # Don't auto-connect; only return keys if already connected
        return ""
    mv_name = MICROVAULT_SERVICES.get(service, service)
    try:
        return bridge.get(mv_name) or ""
    except (KeyError, Exception):
        return ""


def canonical_service(name: str) -> str:
    return SERVICE_ALIASES.get(name.strip().lower(), name.strip().lower())


def mask_key(value: str) -> str:
    if not isinstance(value, str) or len(value) <= 5:
        return "FALTANTE"
    return f"{value[:4]}{'*' * 8} (guardada, {len(value)} caracteres)"


def connect_microvault() -> bool:
    """Explicitly connect to MicroVault (prompts for password).
    Returns True on success."""
    bridge = _get_microvault_bridge()
    if bridge is None:
        print("[!] MicroVault no encontrado.")
        print("    MeXiCOSINT busca MicroVault de dos formas:")
        print("    1. Paquete Python: pip install microvault")
        print("    2. CLI en PATH:    pipx install microvault")
        print("    Si ya lo tienes instalado, verifica que 'microvault' este en tu PATH.")
        return False
    print("[*] Conectando a MicroVault...")
    from mexicosint.microvault_bridge import VaultConnectState

    result = bridge.connect_result()
    if result.state == VaultConnectState.CONNECTED:
        print("[+] MicroVault conectado.")
        return True

    messages = {
        VaultConnectState.NON_INTERACTIVE: (
            "MicroVault necesita una terminal interactiva para pedir la contraseña maestra."
        ),
        VaultConnectState.WRONG_PASSWORD: "La contraseña maestra de MicroVault es incorrecta.",
        VaultConnectState.CORRUPT_VAULT: "No se pudo abrir el vault cifrado de MicroVault.",
        VaultConnectState.TIMEOUT: "MicroVault tardó demasiado tiempo para responder.",
        VaultConnectState.UNAVAILABLE: "MicroVault no está disponible.",
        VaultConnectState.UNKNOWN_ERROR: "No se pudo conectar a MicroVault; verifica el vault interactivamente.",
    }
    print(f"[!] {messages.get(result.state, messages[VaultConnectState.UNKNOWN_ERROR])}")
    return False


def init_config(config_path: Path = CONFIG_PATH, dummy_mode: bool = False,
                use_microvault: bool = False, skip_microvault: bool = False) -> dict:
    if dummy_mode:
        print("[*] Modo dummy: usando configuracion de prueba en memoria.")
        return {k: f"dummy_key_{k}" for k in SAMPLE_CONFIG}

    config = {}

    # ── Layer 1: JSON config file (optional, not created automatically) ──
    if config_path.exists():
        config_stat = config_path.stat()
        current_mode = config_stat.st_mode & 0o777
        if current_mode != 0o600:
            print(f"[!] ADVERTENCIA: Permisos del config son {oct(current_mode)}, deberian ser 0o600.")
            print(f"    Ejecuta: chmod 600 {config_path}")
        with open(config_path, encoding="utf-8") as f:
            config = json.load(f)

    # ── Layer 2: MicroVault (encrypted, auto-detected) ─────────────────
    # No --microvault flag needed: if MicroVault is installed and a
    # service is still missing after the JSON layer, connect automatically
    # (prompts for the master password once). --microvault forces the
    # connection attempt (and hard-fails if it doesn't work); --no-microvault
    # skips MicroVault entirely, even if keys are missing.
    if not skip_microvault:
        missing = [
            service
            for service in SAMPLE_CONFIG
            if not config.get(service) and not _from_env(service)
        ]
        bridge = _get_microvault_bridge()
        if use_microvault or (bridge is not None and missing):
            if not connect_microvault() and use_microvault:
                raise SystemExit(1)
        bridge = _get_microvault_bridge()
        if bridge is not None and bridge._connected:
            print("[*] MicroVault: conectado.")
            for service in SAMPLE_CONFIG:
                if not config.get(service):
                    val = _get_from_microvault(service)
                    if val:
                        config[service] = val

    # ── Layer 3: Environment variables (highest priority) ─────────────
    for service in SAMPLE_CONFIG:
        val = _from_env(service)
        if val:
            config[service] = val

    # ── If nothing configured, guide the user ─────────────────────────
    has_any = any(
        isinstance(v, str) and len(v) > 5
        for k, v in config.items() if k in SAMPLE_CONFIG
    )
    if not has_any:
        print("[!] No se encontraron API keys configuradas.")
        print(f"    Opciones:")
        print(f"    1. MicroVault:  microvault add <servicio>")
        print(f"    2. Variables de entorno: export MEXICOSINT_GEOAPIFY_API_KEY=tu_key")
        print(f"    3. Archivo JSON: crear {config_path} con tus keys")
        print(f"    Servicios: {', '.join(SAMPLE_CONFIG)}")
        if not config_path.exists():
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(SAMPLE_CONFIG, f, indent=2, ensure_ascii=False)
            os.chmod(config_path, stat.S_IRUSR | stat.S_IWUSR)
            print(f"    Archivo de ejemplo creado: {config_path}")
        raise SystemExit(0)

    return config


def check_keys(config: dict, dummy_mode: bool = False) -> list[str]:
    print("\n[*] Estado de API Keys:")
    active = []
    canonical_config = {}
    for key, value in config.items():
        canonical = canonical_service(key)
        canonical_config.setdefault(canonical, value)

    for key, value in canonical_config.items():
        if dummy_mode:
            print(f"    {key:30} CONFIGURED_UNVERIFIED (dummy; fixture)")
            active.append(key)
        elif isinstance(value, str) and len(value) > 5:
            source = get_credential_source(key, config)
            print(f"    {key:30} CONFIGURED_UNVERIFIED ({source})")
            active.append(key)
        else:
            print(f"    {key:30} MISSING")
    if not dummy_mode:
        print("[*] Las keys se validan solo al usarlas durante un escaneo real.")
        print("    No se hacen llamadas extra para comprobar credenciales.")
    return active


def get_api_key(config: dict, key: str) -> str:
    # 1. Environment variable (highest priority)
    val = _from_env(key)
    if val:
        return val

    # 2. MicroVault
    val = _get_from_microvault(key)
    if val:
        return val

    # 3. JSON config (with legacy alias support)
    if config.get(key):
        return config[key]
    legacy = {alias: canonical for alias, canonical in SERVICE_ALIASES.items() if canonical == key}
    for alias in legacy:
        if config.get(alias):
            return config[alias]
    return ""


def get_credential_source(
    service: str,
    config: dict | None = None,
    dummy_mode: bool = False,
) -> str:
    """Return non-secret credential source metadata for status reporting."""
    if dummy_mode:
        return "dummy"
    if _from_env(service):
        return "environment"
    if _get_from_microvault(service):
        return "microvault"
    if config:
        if config.get(service):
            return "json"
        for alias, canonical in SERVICE_ALIASES.items():
            if canonical == service and config.get(alias):
                return "json"
    return "missing"


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
