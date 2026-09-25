#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MeXicOSINT v2.7.1
Herramienta de OSINT para numeros telefonicos Mexicanos
Autor: KiMiGuEL

Cambios v2.7.1:
  - Refactor de nucleo con ScanSettings, modulos de proveedor y presentacion
  - Estados estructurados de proveedores, errores sanitizados y fuente de geocodificacion
  - Fallback de NumVerify/APILayer al endpoint marketplace
  - Mejoras de diagnostico MicroVault y perfil aislado

Cambios v2.7.0:
  - MicroVault ya no requiere el flag --microvault: se auto-detecta y se
    conecta para resolver el perfil requerido. --microvault fuerza la conexion.
  - Bridge (microvault_bridge.py) usa estrictamente el perfil "mexicosint"
    de MicroVault con `microvault env --profile mexicosint --json`; no hay
    fallback bare/per-service ni variables de entorno/JSON como credenciales
  - --dummy-test sigue existiendo para depuracion interna pero ya no se
    documenta publicamente (--help, README, docs/)

Cambios v2.6.0:
  - MicroVault integration: --microvault flag + bridge module para leer
    credenciales desde el perfil cifrado "mexicosint"
  - Mapeo de nombres de servicio de MicroVault (abstract_api, numverify_api,
    opencage_api, ipgs) alineado con la convencion del vault
  - Fallback de geocodificacion GPS: intenta LADA, ciudad de consenso y
    region phonenumbers cuando la localidad canonica es vacia o vaga
  - Cosmetico: consola unificada, separadores entre secciones, sin filas
    vacias, advertencia de portabilidad en una linea
  - Limpieza: dependencias sin uso removidas (beautifulsoup4, python-dotenv,
    lxml), MIGRATION.md eliminado, docs actualizadas (flag -b removido)

Cambios v2.5.6:
  - MicroVault integration: API keys can be read from MicroVault (encrypted
    vault) via Python import or CLI subprocess bridge (works with pipx)
  - --microvault flag: explicit MicroVault connection (prompts for password)
  - Key resolution order: solo el perfil MicroVault "mexicosint"
  - GPS geocoding fallback: tries LADA region, consensus city, phonenumbers
    region when canonical locality query is empty or vague
  - Cosmetic: unified Console instance, Rule separators, removed spacer rows,
    compressed portability warning to single line
  - Updated --help with current options and key resolution documentation

Cambios v2.5.5:
  - Corregida fuga de API keys: errores de proveedores fallidos escribian
    la key en texto plano en los reportes JSON exportados; ahora se redacta
  - Unificado LADA_MAP duplicado (main.py + local_parser.py) en una sola
    fuente (data/lada.py); corregidos 5 codigos con ciudad/estado incorrectos
  - Clase base Provider[T] para proveedores; enum EvidenceState
  - Eliminado el banner compacto (--small-banner); un solo diseno
  - Eliminado modulo muerto quienhabla.py

Cambios v2.5.4:
  - Base IFT/PNN actualizada al corte del 05/09/2026 (178,172 bloques geograficos,
    1,565 bloques no geograficos)
  - Removido modulo muerto ift_sns.py (SQLite legacy, reemplazado por ift_blocks.py)

Cambios v2.5.3:
  - Llamadas a APIs concurrentes con asyncio + aiohttp (fase telefonica en paralelo)
  - Geocodificadores OpenCage/Geoapify en paralelo; Nominatim sigue como respaldo final
  - Pooling de conexiones: aiohttp.ClientSession (async) y requests.Session compartida (sync)
  - Memoizacion de normalizacion de ciudades y filtros de localidad (lru_cache)
  - Cache de geocodificacion Nominatim (sync y async)
  - Creacion perezosa de directorios de salida (solo al generar reporte/mapa)
  - Copias superficiales en modo dummy (sin deepcopy)
  - Regex precompiladas en filtros de localidad

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

import asyncio
import aiohttp
import sys
import urllib.parse
import uuid
from datetime import datetime
from dataclasses import asdict

from mexicosint import config as config_store
from mexicosint.core.scan_result import ScanResult
from mexicosint.core.settings import ScanSettings
from mexicosint.data.lada import get_locality_str
from mexicosint.evidence import EvidenceState, SourceVote, decide_evidence, normalize_city
from mexicosint.locality import (
    clean_place_name as _clean_place_name,
    is_concrete_locality as _is_concrete_locality,
    split_lada_region as _split_lada_region,
)
from mexicosint.numbering import normalize_mx_number
from mexicosint.modules.local_parser import parse_mx_number
from mexicosint.providers.abstract import (
    SAMPLE_ABSTRACT_INTEL,
    AbstractPhoneIntelligenceProvider,
    parse_abstract,
)
from mexicosint.providers.geoapify import GeoapifyProvider
from mexicosint.providers.ipqualityscore import IPQualityScoreProvider
from mexicosint.providers.numverify import (
    SAMPLE_NUMVERIFY,
    NumVerifyProvider,
    parse_numverify,
)
from mexicosint.providers.nominatim import geocode_nominatim
from mexicosint.providers.opencage import OpenCageProvider
from mexicosint.providers.status import (
    ProviderState,
    ProviderStatus,
    classify_provider_exception,
)
from mexicosint.presentation import (
    _render_figlet,
    _rich_or_plain,
    _section_break,
    plain_print_api_results,
    plain_print_consensus,
    plain_print_errors,
    plain_print_geo,
    plain_print_osint_links,
    plain_print_provider_states,
    plain_print_report,
    plain_print_subscriber,
    print_banner,
    print_results,
    rich_print_api_results,
    rich_print_consensus,
    rich_print_errors,
    rich_print_geo,
    rich_print_osint_links,
    rich_print_provider_states,
    rich_print_report,
    rich_print_subscriber,
)
from mexicosint.reporting import generate_map, save_report

try:
    from mexicosint.modules.ift_blocks import lookup_block, modality_label
    IFT_BLOCKS_AVAILABLE = True
except ImportError:
    IFT_BLOCKS_AVAILABLE = False

SAMPLE_CONFIG = config_store.SAMPLE_CONFIG


def _sanitize_error(text: str, api_key: str | None) -> str:
    """Redact an API key from an error message before it's stored/exported.

    HTTP error exceptions (raise_for_status, aiohttp) include the full
    request URL in their string form, and every provider here sends its
    key as a query param or (IPQualityScore) embedded in the URL path.
    Without this, a failed API call leaks the live key into the exported
    JSON report.
    """
    if not api_key:
        return text
    redacted = text.replace(api_key, "***REDACTED***")
    for encoded in {
        urllib.parse.quote(api_key, safe=""),
        urllib.parse.quote_plus(api_key),
    }:
        if encoded != api_key:
            redacted = redacted.replace(encoded, "***REDACTED***")
    return redacted


# --- SAMPLE DATA (DUMMY MODE) ---
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

def init_config(
    use_microvault: bool = False,
    settings: ScanSettings | None = None,
):
    settings = settings or ScanSettings()
    return config_store.init_config(
        settings.dummy_mode,
        use_microvault=use_microvault,
    )


def check_keys(config, settings: ScanSettings | None = None):
    settings = settings or ScanSettings()
    return config_store.check_keys(config, settings.dummy_mode)


def _get_api_key(config, key):
    return config_store.get_api_key(config, key)


# --- API KEY MANAGEMENT ---
# MeXiCOSINT does not manage credentials. The supported provider is MicroVault
# and its required ``mexicosint`` profile; the CLI intentionally has no
# plaintext key store or key-management command.


# --- MEXICO LADA DATABASE (FIX #4: Official IFT data) ---
# Source: Instituto Federal de Telecomunicaciones (IFT) - Plan Nacional de Numeracion

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
    return get_locality_str(lada3) or get_locality_str(lada2) or ""


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


PROVIDER_DISPLAY_NAMES = {
    "abstract_phone_intelligence": "AbstractAPI",
    "numverify": "NumVerify",
    "opencage": "OpenCage",
    "geoapify": "Geoapify",
    "ipqualityscore": "IPQualityScore",
}


def _initialize_provider_states(
    result: ScanResult,
    config: dict,
    active: list[str],
    settings: ScanSettings,
) -> None:
    for service in SAMPLE_CONFIG:
        source = config_store.get_credential_source(
            service,
            config,
            dummy_mode=settings.dummy_mode,
        )
        state = (
            ProviderState.CONFIGURED_UNVERIFIED
            if service in active
            else ProviderState.MISSING
        )
        result.provider_states[service] = ProviderStatus(
            state=state,
            source=source,
        )
    result.provider_states["nominatim"] = ProviderStatus(
        state=ProviderState.NOT_REQUESTED,
        source="keyless",
    )


def _set_provider_state(
    result: ScanResult,
    service: str,
    status: ProviderStatus,
) -> None:
    previous = result.provider_states.get(service)
    if previous and not status.source:
        status = ProviderStatus(
            state=status.state,
            source=previous.source,
            transport=status.transport,
            request_attempted=status.request_attempted,
            http_status=status.http_status,
            provider_code=status.provider_code,
            detail=status.detail,
        )
    result.provider_states[service] = status


def _provider_error_status(
    exc: Exception,
    api_key: str | None,
) -> ProviderStatus:
    status = classify_provider_exception(exc)
    return ProviderStatus(
        state=status.state,
        source="",
        transport=status.transport,
        request_attempted=status.request_attempted,
        http_status=status.http_status,
        provider_code=status.provider_code,
        detail=_sanitize_error(status.detail, api_key),
    )


# --- CANONICAL LOCALITY ---
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


async def _lookup_cached_geocoder_async(provider, session, locality: str):
    """Async variant: uses provider.alookup when available, else the sync lookup in a thread."""
    alookup = getattr(provider, "alookup", None)
    if alookup is None:
        return await asyncio.to_thread(_lookup_cached_geocoder, provider, locality)
    cache = provider._async_cache
    key = (provider.api_key, locality)
    hit = key in cache
    evidence = await alookup(session, locality)
    return evidence, "cache_hit" if hit else "cache_miss"


async def _call_maybe_async(fn, *args, session):
    """Call fn's async twin (fn.async_impl) when defined, else run sync fn in a thread.

    Keeps monkeypatched/test fakes working: only the real implementations carry
    an async_impl attribute.
    """
    impl = getattr(fn, "async_impl", None)
    if impl is not None:
        return await impl(session, *args)
    return await asyncio.to_thread(fn, *args)


# --- API CALLS (compatibility wrappers over provider classes) ---
def abstract_phone_intelligence_lookup(
    e164, api_key, settings: ScanSettings | None = None
):
    settings = settings or ScanSettings()
    if settings.dummy_mode:
        return dict(SAMPLE_ABSTRACT_INTEL)
    return AbstractPhoneIntelligenceProvider(
        api_key,
        timeout=settings.default_timeout,
        session=settings.session,
    ).lookup(e164)


async def _abstract_intel_async(session, e164, api_key):
    provider = AbstractPhoneIntelligenceProvider(api_key)
    return await provider.alookup(session, e164)


abstract_phone_intelligence_lookup.async_impl = _abstract_intel_async


def numverify_lookup(
    e164, api_key, settings: ScanSettings | None = None
):
    settings = settings or ScanSettings()
    if settings.dummy_mode:
        return dict(SAMPLE_NUMVERIFY)
    return NumVerifyProvider(
        api_key,
        timeout=settings.default_timeout,
        session=settings.session,
    ).lookup(e164)


async def _numverify_async(session, e164, api_key):
    provider = NumVerifyProvider(api_key)
    return await provider.alookup(session, e164)


numverify_lookup.async_impl = _numverify_async


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
            result.evidence_state = EvidenceState.STRONG_AGREEMENT
        elif agreeing and conflicting:
            result.evidence_state = EvidenceState.PARTIAL_AGREEMENT
        elif conflicting:
            result.evidence_state = EvidenceState.CONFLICTING_SOURCES
        else:
            result.evidence_state = EvidenceState.SINGLE_SOURCE
    else:
        result.consensus_city = decision.city
        result.consensus_confidence = 0.0
        result.consensus_sources = decision.sources
        result.evidence_state = decision.state


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


# --- NETWORK PHASE (async orchestration) ---
# Phone APIs and geocoders run concurrently via asyncio + aiohttp.
# Sync module-level lookups/providers remain as fallback (tests, embedders):
# _call_maybe_async uses fn.async_impl when defined, else a worker thread.


async def _abstract_job(result, normalized, e164, config, active, session, api_results):
    service = "abstract_phone_intelligence"
    if service not in active:
        _trace_provider(result, "AbstractAPI", "skipped", normalized)
        return
    key = _get_api_key(config, service)
    try:
        _trace_provider(result, "AbstractAPI", "live_request", normalized)
        api_results["abstract_intel"] = await _call_maybe_async(
            abstract_phone_intelligence_lookup,
            e164,
            key,
            session=session,
        )
        _set_provider_state(
            result,
            service,
            ProviderStatus(
                state=ProviderState.REQUEST_SUCCESS,
                transport="live_request",
                request_attempted=True,
            ),
        )
    except Exception as exc:
        api_results["abstract_intel"] = None
        status = _provider_error_status(exc, key)
        _set_provider_state(result, service, status)
        result.errors.append(f"abstract_intel: {status.detail}")
        _trace_provider(
            result,
            "AbstractAPI",
            str(status.state),
            normalized,
            note=type(exc).__name__,
        )


async def _numverify_job(result, normalized, e164, config, active, session, api_results):
    service = "numverify"
    if service not in active:
        _trace_provider(result, "NumVerify", "skipped", normalized)
        return
    key = _get_api_key(config, service)
    try:
        _trace_provider(result, "NumVerify", "live_request", normalized)
        api_results["numverify"] = await _call_maybe_async(
            numverify_lookup,
            e164,
            key,
            session=session,
        )
        _set_provider_state(
            result,
            service,
            ProviderStatus(
                state=ProviderState.REQUEST_SUCCESS,
                transport="live_request",
                request_attempted=True,
            ),
        )
    except Exception as exc:
        api_results["numverify"] = None
        status = _provider_error_status(exc, key)
        _set_provider_state(result, service, status)
        result.errors.append(f"numverify: {status.detail}")
        _trace_provider(
            result,
            "NumVerify",
            str(status.state),
            normalized,
            note=type(exc).__name__,
        )


async def _ipqs_job(result, normalized, config, active, session, settings):
    service = "ipqualityscore"
    if service not in active:
        _trace_provider(result, "IPQualityScore", "skipped", normalized)
        return
    key = _get_api_key(config, service)
    try:
        _trace_provider(result, "IPQualityScore", "live_request", normalized)
        provider = IPQualityScoreProvider(key)
        alookup = getattr(provider, "alookup", None)
        if alookup is not None:
            reputation = await alookup(session, normalized)
        else:
            reputation = await asyncio.to_thread(provider.lookup, normalized)
        if reputation:
            result.ipqualityscore_data = asdict(reputation)
            state = ProviderState.REQUEST_SUCCESS
        else:
            state = ProviderState.NO_RESULT
        _set_provider_state(
            result,
            service,
            ProviderStatus(
                state=state,
                transport="live_request",
                request_attempted=True,
            ),
        )
    except Exception as exc:
        status = _provider_error_status(exc, key)
        _set_provider_state(result, service, status)
        result.errors.append(f"ipqualityscore: {status.detail}")
        _trace_provider(
            result,
            "IPQualityScore",
            str(status.state),
            normalized,
            note=status.detail or type(exc).__name__,
        )


async def _opencage_job(result, normalized, geo_target, config, session, settings):
    service = "opencage"
    key = _get_api_key(config, service)
    try:
        locality, transport = await _lookup_cached_geocoder_async(
            OpenCageProvider(key),
            session,
            geo_target,
        )
        state = (
            ProviderState.REQUEST_SUCCESS
            if locality
            else ProviderState.NO_RESULT
        )
        _set_provider_state(
            result,
            service,
            ProviderStatus(
                state=state,
                transport=transport,
                request_attempted=transport != "cache_hit",
            ),
        )
        _trace_provider(
            result,
            "OpenCage",
            str(state),
            normalized,
            locality_query=geo_target,
            note=transport,
        )
        if locality:
            result.opencage_data = asdict(locality)
            result.opencage_latitude = locality.latitude
            result.opencage_longitude = locality.longitude
            result.opencage_address = locality.formatted_address
    except Exception as exc:
        status = _provider_error_status(exc, key)
        _set_provider_state(result, service, status)
        result.errors.append(f"opencage: {status.detail}")
        _trace_provider(
            result,
            "OpenCage",
            str(status.state),
            normalized,
            locality_query=geo_target,
            note=type(exc).__name__,
        )


async def _geoapify_job(result, normalized, geo_target, config, session, settings):
    service = "geoapify"
    key = _get_api_key(config, service)
    try:
        locality, transport = await _lookup_cached_geocoder_async(
            GeoapifyProvider(key),
            session,
            geo_target,
        )
        state = (
            ProviderState.REQUEST_SUCCESS
            if locality
            else ProviderState.NO_RESULT
        )
        _set_provider_state(
            result,
            service,
            ProviderStatus(
                state=state,
                transport=transport,
                request_attempted=transport != "cache_hit",
            ),
        )
        _trace_provider(
            result,
            "Geoapify",
            str(state),
            normalized,
            locality_query=geo_target,
            note=transport,
        )
        if locality:
            result.geoapify_data = asdict(locality)
            result.geoapify_latitude = locality.latitude
            result.geoapify_longitude = locality.longitude
            result.geoapify_address = locality.formatted_address
    except Exception as exc:
        status = _provider_error_status(exc, key)
        _set_provider_state(result, service, status)
        result.errors.append(f"geoapify: {status.detail}")
        _trace_provider(
            result,
            "Geoapify",
            str(status.state),
            normalized,
            locality_query=geo_target,
            note=type(exc).__name__,
        )


async def _run_network_phase(
    result,
    normalized,
    e164,
    config,
    active,
    settings: ScanSettings,
):
    """Phone-API fan-out, parsing, consensus and geocoding.

    Phone APIs (Abstract, NumVerify, IPQualityScore) run concurrently, then
    OpenCage + Geoapify run concurrently; Nominatim stays the final fallback.
    """
    api_results = {}

    if settings.dummy_mode:
        if "abstract_phone_intelligence" in active:
            _trace_provider(result, "AbstractAPI", "fixture", normalized)
            api_results["abstract_intel"] = abstract_phone_intelligence_lookup(
                e164,
                _get_api_key(config, "abstract_phone_intelligence"),
                settings,
            )
            _set_provider_state(
                result,
                "abstract_phone_intelligence",
                ProviderStatus(
                    state=ProviderState.REQUEST_SUCCESS,
                    transport="fixture",
                ),
            )
        else:
            _trace_provider(result, "AbstractAPI", "skipped", normalized)
        if "numverify" in active:
            _trace_provider(result, "NumVerify", "fixture", normalized)
            api_results["numverify"] = numverify_lookup(
                e164, _get_api_key(config, "numverify"), settings
            )
            _set_provider_state(
                result,
                "numverify",
                ProviderStatus(
                    state=ProviderState.REQUEST_SUCCESS,
                    transport="fixture",
                ),
            )
        else:
            _trace_provider(result, "NumVerify", "skipped", normalized)
        if "ipqualityscore" in active:
            _trace_provider(result, "IPQualityScore", "fixture", normalized)
            result.ipqualityscore_data = dict(SAMPLE_IPQUALITYSCORE)
            _set_provider_state(
                result,
                "ipqualityscore",
                ProviderStatus(
                    state=ProviderState.REQUEST_SUCCESS,
                    transport="fixture",
                ),
            )
        else:
            _trace_provider(result, "IPQualityScore", "skipped", normalized)
    else:
        async with aiohttp.ClientSession() as session:
            await asyncio.gather(
                _abstract_job(result, normalized, e164, config, active, session, api_results),
                _numverify_job(result, normalized, e164, config, active, session, api_results),
                _ipqs_job(result, normalized, config, active, session, settings),
            )

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

    # Geocode: try canonical locality first, fall back to LADA/consensus/phonenumbers.
    geo_target = result.canonical_locality_query

    if not geo_target or not _is_concrete_locality(geo_target):
        # Fallback chain: LADA region → consensus city → phonenumbers region
        for candidate in (result.lada_region, result.consensus_city, result.region_phonenumbers):
            if candidate and _is_concrete_locality(candidate):
                geo_target = candidate if "," in candidate else f"{candidate}, Mexico"
                break

    if not geo_target or not _is_concrete_locality(geo_target):
        result.geocoding_source = "unavailable"
        _set_provider_state(
            result,
            "nominatim",
            ProviderStatus(
                state=ProviderState.NOT_REQUESTED,
                detail="no_concrete_locality",
            ),
        )
        _trace_provider(result, "OpenCage", "skipped", normalized, locality_query=geo_target or "", note="no_concrete_locality")
        _trace_provider(result, "Geoapify", "skipped", normalized, locality_query=geo_target or "", note="no_concrete_locality")
        _trace_provider(result, "Nominatim", "skipped", normalized, locality_query=geo_target or "", note="no_concrete_locality")
    elif geo_target:
        if settings.dummy_mode:
            print("\n[*] Geocodificando localidad...")
            print("    [!] Omitido en modo dummy para evitar llamadas de red.")
            if "opencage" in active:
                _trace_provider(result, "OpenCage", "fixture", normalized, locality_query=geo_target)
                _set_provider_state(
                    result,
                    "opencage",
                    ProviderStatus(
                        state=ProviderState.REQUEST_SUCCESS,
                        transport="fixture",
                    ),
                )
            else:
                _trace_provider(result, "OpenCage", "skipped", normalized, locality_query=geo_target)
            if "geoapify" in active:
                _trace_provider(result, "Geoapify", "fixture", normalized, locality_query=geo_target)
                result.geoapify_data = dict(SAMPLE_GEOAPIFY)
                _set_provider_state(
                    result,
                    "geoapify",
                    ProviderStatus(
                        state=ProviderState.REQUEST_SUCCESS,
                        transport="fixture",
                    ),
                )
            else:
                _trace_provider(result, "Geoapify", "skipped", normalized, locality_query=geo_target)
            _set_provider_state(
                result,
                "nominatim",
                ProviderStatus(
                    state=ProviderState.NOT_REQUESTED,
                    detail="dummy_mode",
                ),
            )
            _trace_provider(result, "Nominatim", "skipped", normalized, locality_query=geo_target)
            result.geocoding_source = "fixture"
        else:
            print("\n[*] Geocodificando localidad de numeracion (OpenCage y Geoapify en paralelo, Nominatim final)...")
            async with aiohttp.ClientSession() as session:
                jobs = []
                if "opencage" in active:
                    jobs.append(
                        _opencage_job(
                            result,
                            normalized,
                            geo_target,
                            config,
                            session,
                            settings,
                        )
                    )
                else:
                    _trace_provider(result, "OpenCage", "skipped", normalized, locality_query=geo_target)
                if "geoapify" in active:
                    jobs.append(
                        _geoapify_job(
                            result,
                            normalized,
                            geo_target,
                            config,
                            session,
                            settings,
                        )
                    )
                else:
                    _trace_provider(result, "Geoapify", "skipped", normalized, locality_query=geo_target)
                if jobs:
                    await asyncio.gather(*jobs)

                # OpenCage stays primary; Geoapify is the backup.
                if result.opencage_latitude and result.opencage_longitude:
                    result.latitude, result.longitude = result.opencage_latitude, result.opencage_longitude
                    result.geocoding_source = "OpenCage"
                    print("    [OpenCage] OK")
                elif result.geoapify_latitude and result.geoapify_longitude:
                    result.latitude, result.longitude = result.geoapify_latitude, result.geoapify_longitude
                    result.geocoding_source = "Geoapify"
                    print("    [Geoapify] OK")

                if not result.latitude or not result.longitude:
                    print("    [OpenCage/Geoapify] Sin key/resultado, usando Nominatim...")
                    _trace_provider(result, "Nominatim", "live_request", normalized, locality_query=geo_target)
                    try:
                        result.latitude, result.longitude, result.nominatim_address = await _call_maybe_async(
                            geocode_nominatim,
                            geo_target,
                            session=session,
                        )
                    except Exception as exc:
                        result.geocoding_source = "unavailable"
                        status = _provider_error_status(exc, None)
                        _set_provider_state(result, "nominatim", status)
                        result.errors.append(f"nominatim: {status.detail}")
                        _trace_provider(
                            result,
                            "Nominatim",
                            str(status.state),
                            normalized,
                            locality_query=geo_target,
                            note=type(exc).__name__,
                        )
                    else:
                        if result.latitude and result.longitude:
                            result.geocoding_source = "Nominatim"
                            _set_provider_state(
                                result,
                                "nominatim",
                                ProviderStatus(
                                    state=ProviderState.REQUEST_SUCCESS,
                                    transport="live_request",
                                    request_attempted=True,
                                ),
                            )
                            _trace_provider(
                                result,
                                "Nominatim",
                                str(ProviderState.REQUEST_SUCCESS),
                                normalized,
                                locality_query=geo_target,
                            )
                        else:
                            result.geocoding_source = "unavailable"
                            _set_provider_state(
                                result,
                                "nominatim",
                                ProviderStatus(
                                    state=ProviderState.NO_RESULT,
                                    transport="live_request",
                                    request_attempted=True,
                                ),
                            )
                            _trace_provider(
                                result,
                                "Nominatim",
                                str(ProviderState.NO_RESULT),
                                normalized,
                                locality_query=geo_target,
                            )
                else:
                    _set_provider_state(
                        result,
                        "nominatim",
                        ProviderStatus(
                            state=ProviderState.NOT_REQUESTED,
                            detail="another_geocoder_succeeded",
                        ),
                    )
                    _trace_provider(result, "Nominatim", "skipped", normalized, locality_query=geo_target)


# --- MAIN ---
def run_phone_scan(
    raw: str,
    config: dict,
    active: list,
    settings: ScanSettings | None = None,
) -> ScanResult:
    settings = settings or ScanSettings()
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
    _initialize_provider_states(result, config, active, settings)

    # API calls + geocoding (concurrent network phases)
    asyncio.run(_run_network_phase(result, normalized, e164, config, active, settings))

    # Map
    if result.latitude and result.longitude:
        result.map_path = generate_map(result, settings)

    # Report
    result.report_path = save_report(result, settings)

    return result


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    dummy_mode = False
    use_microvault = False

    if "--dummy-test" in args:
        dummy_mode = True
        args.remove("--dummy-test")
        print("\n[!] MODO DUMMY ACTIVADO: No se realizaran llamadas reales a las APIs.")
        print("    Se usaran datos de ejemplo. No se consumiran creditos.\n")

    if "--microvault" in args:
        use_microvault = True
        args.remove("--microvault")

    settings = ScanSettings(dummy_mode=dummy_mode)

    print_banner()

    number = args[0] if args else None

    if not number:
        print("Uso: mexicosint [opciones] <numero_mexicano>")
        print("     mexicosint 5512345678")
        print("     mexicosint --microvault 5512345678")
        print("     mexicosint --help")
        sys.exit(1)

    print(f"[+] Fecha/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    config = init_config(
        use_microvault=use_microvault,
        settings=settings,
    )
    active = check_keys(config, settings)

    if number:
        print(f"[+] Entrada cruda: {number}")
        print("=" * 60)
        result = run_phone_scan(number, config, active, settings)
        print_results(result)

    print("\n[*] Escaneo completado.")
    print("=" * 60)


if __name__ == "__main__":
    main()
