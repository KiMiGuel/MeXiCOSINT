"""MicroVault-only credential resolution for MeXiCOSINT.

Normal scans obtain provider credentials from the MicroVault ``mexicosint``
profile through :mod:`mexicosint.microvault_bridge`.  Generic environment
variables and plaintext JSON files are deliberately not credential sources.
The in-memory mapping returned by this module is only a snapshot of the
already-authorized MicroVault profile; it is never persisted.
"""

from __future__ import annotations

# Provider names are also used as in-memory dummy-mode fixtures; no credential
# values are stored here for normal scans.
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

# MeXiCOSINT service names -> names used in the mexicosint MicroVault profile.
MICROVAULT_SERVICES = {
    "abstract_phone_intelligence": "abstract_api",
    "numverify": "numverify_api",
    "opencage": "opencage_api",
    "geoapify": "geoapify",
    "ipqualityscore": "ipgs",
}

# Lazy-loaded bridge.  It is deliberately never initialized with a direct
# environment lookup: the bridge owns the only supported credential source.
_mv_bridge = None


def _get_microvault_bridge():
    """Return the shared MicroVault bridge when MicroVault is available."""
    global _mv_bridge
    if _mv_bridge is not None:
        return _mv_bridge if _mv_bridge.is_available() else None
    from mexicosint.microvault_bridge import get_bridge

    _mv_bridge = get_bridge()
    return _mv_bridge if _mv_bridge.is_available() else None


def _get_from_microvault(service: str) -> str:
    """Read a service from the unlocked ``mexicosint`` profile snapshot."""
    bridge = _get_microvault_bridge()
    if bridge is None or not bridge.is_connected:
        return ""
    try:
        return bridge.get(MICROVAULT_SERVICES.get(service, service)) or ""
    except Exception:
        # A missing profile/service must not expose vault internals or a key.
        return ""


def canonical_service(name: str) -> str:
    return SERVICE_ALIASES.get(name.strip().lower(), name.strip().lower())


def mask_key(value: str) -> str:
    if not isinstance(value, str) or len(value) <= 5:
        return "FALTANTE"
    return f"{value[:4]}{'*' * 8} (guardada, {len(value)} caracteres)"


def connect_microvault() -> bool:
    """Prompt for and unlock the required ``mexicosint`` MicroVault profile."""
    bridge = _get_microvault_bridge()
    if bridge is None:
        print("[!] MicroVault no está disponible.")
        print("    MeXiCOSINT requiere MicroVault para el enriquecimiento normal.")
        print("    Instala MicroVault y crea el perfil: mexicosint")
        return False

    print("[*] Conectando al perfil MicroVault 'mexicosint'...")
    result = bridge.connect_result()
    if result.state.value == "connected":
        print("[+] MicroVault conectado.")
        return True

    messages = {
        "non_interactive": "MicroVault necesita una terminal interactiva para pedir la contraseña maestra.",
        "wrong_password": "La contraseña maestra de MicroVault es incorrecta.",
        "corrupt_vault": "No se pudo abrir el vault cifrado de MicroVault.",
        "timeout": "MicroVault tardó demasiado tiempo para responder.",
        "unavailable": "MicroVault no está disponible.",
    }
    print(f"[!] {messages.get(result.state.value, 'No se pudo conectar al perfil MicroVault.')}")
    return False


def init_config(
    dummy_mode: bool = False,
    use_microvault: bool = False,
) -> dict:
    """Return the authorized MicroVault profile, or dummy fixtures.

    There is intentionally no filesystem credential I/O. Missing MicroVault
    means no provider enrichment, not a
    plaintext fallback.
    """
    if dummy_mode:
        print("[*] Modo dummy: usando configuración de prueba en memoria.")
        return {service: f"dummy_key_{service}" for service in SAMPLE_CONFIG}

    bridge = _get_microvault_bridge()
    if bridge is None:
        print("[!] MicroVault no está disponible; no se puede enriquecer.")
        return {}

    if not connect_microvault():
        if use_microvault:
            raise SystemExit(1)
        return {}

    profile = {
        service: _get_from_microvault(service)
        for service in SAMPLE_CONFIG
    }
    profile = {service: value for service, value in profile.items() if value}
    if not profile:
        print("[!] El perfil MicroVault 'mexicosint' no contiene keys utilizables.")
        print("    Configúralo con: microvault profile mexicosint geoapify opencage_api ipgs numverify_api abstract_api")
    return profile


def check_keys(config: dict, dummy_mode: bool = False) -> list[str]:
    print("\n[*] Estado de API Keys:")
    active = []
    canonical_config = {}
    for key, value in config.items():
        canonical_config.setdefault(canonical_service(key), value)

    for key, value in canonical_config.items():
        if dummy_mode:
            source = "dummy"
        elif isinstance(value, str) and len(value) > 5:
            source = "microvault"
        else:
            source = "missing"
        state = "CONFIGURED_UNVERIFIED" if source != "missing" else "MISSING"
        print(f"    {key:30} {state} ({source})")
        if source != "missing":
            active.append(key)
    if not dummy_mode:
        print("[*] Las keys se validan solo al usarlas durante un escaneo real.")
        print("    No se hacen llamadas extra para comprobar credenciales.")
    return active


def get_api_key(config: dict, key: str) -> str:
    """Return a key from the in-memory MicroVault profile snapshot.

    ``config`` is produced by :func:`init_config`; callers must not treat it as
    a file-backed source.  Keeping this small API preserves provider adapters
    and dummy fixtures without reintroducing environment/JSON fallbacks.
    """
    canonical = canonical_service(key)
    if config.get(canonical):
        return config[canonical]
    if config.get(key):
        return config[key]
    return ""


def get_credential_source(
    service: str,
    config: dict | None = None,
    dummy_mode: bool = False,
) -> str:
    """Return non-secret credential source metadata for status reporting."""
    if dummy_mode:
        return "dummy"
    if config and config.get(canonical_service(service)):
        return "microvault"
    return "missing"
