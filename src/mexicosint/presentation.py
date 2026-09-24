"""Terminal presentation for MeXiCOSINT scan results."""

from __future__ import annotations

import sys

from mexicosint import __version__
from mexicosint.core.scan_result import ScanResult

try:
    from rich import box
    from rich.console import Console
    from rich.rule import Rule
    from rich.table import Table

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

_console = Console() if RICH_AVAILABLE else None

GREEN = "\033[1;32m"
WHITE = "\033[1;37m"
RED = "\033[1;31m"
RESET = "\033[0m"


def _render_figlet(text, font_arg):
    import subprocess

    try:
        result = subprocess.run(
            ["figlet", "-f", font_arg, text],
            capture_output=True,
            text=True,
            timeout=5,
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

    chosen_lines = _render_figlet("MeXicOSINT", "small")
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
            mid = line[third : 2 * third]
            right = line[2 * third :]
            colored = f"{GREEN}{left}{WHITE}{mid}{RED}{right}{RESET}"
            print(f"{GREEN}║  {colored}{' ' * padding}  {RED}║{RESET}")
        print(bottom)
        print(f"{WHITE}         OSINT para numeros telefonicos Mexicanos{RESET}")
        print(f"{RED}                   Autor: KiMiGuEL{RESET}")
        print()
        return

    box_width = max(min(68, term_width - 2), 20)
    print()
    print(GREEN + "╔" + "═" * box_width + "╗" + RESET)
    print(WHITE + "║" + f"MeXicOSINT v{__version__}".center(box_width) + "║" + RESET)
    print(RED + "║" + "OSINT para numeros Mexicanos".center(box_width) + "║" + RESET)
    print(RED + "║" + "Autor: KiMiGuEL".center(box_width) + "║" + RESET)
    print(RED + "╚" + "═" * box_width + "╝" + RESET)
    print()


def _rich_or_plain(rich_func, plain_func):
    if RICH_AVAILABLE and sys.stdout.isatty():
        try:
            rich_func()
            return
        except Exception:
            pass
    plain_func()


def rich_print_subscriber(result: ScanResult):
    table = Table(
        title="📋 INFORMACION DEL SUSCRIPTOR",
        box=box.HEAVY_EDGE,
        title_style="bold cyan",
        border_style="bright_blue",
        show_lines=True,
    )
    table.add_column("Campo", style="bold yellow", width=28)
    table.add_column("Valor", style="bold white", width=50)
    table.add_row("Scan ID", result.scan_id)
    table.add_row("Timestamp (UTC)", result.scan_timestamp)
    table.add_row("MSISDN (E.164)", f"[bold]{result.e164}[/bold]")
    table.add_row("Valido", "[green]SI[/green]" if result.valid else "[red]NO[/red]")
    table.add_row("Region (phonenumbers)", result.region_phonenumbers or "—")
    table.add_row("Region LADA (ref.)", result.lada_region or "—")
    if result.ift_carrier:
        table.add_row(
            "Operadora (IFT oficial)",
            f"[bold green]{result.ift_carrier}[/bold green]",
        )
    if result.ift_modality:
        table.add_row("Modalidad (IFT)", result.ift_modality)
    if result.ift_fecha_asignacion:
        table.add_row("Asignado (IFT)", result.ift_fecha_asignacion)
    if result.ift_service_type:
        table.add_row(
            "Tipo de servicio (IFT)",
            f"[bold red]{result.ift_service_type}[/bold red]",
        )
    table.add_row("Operadora (Abstract)", result.abstract_carrier or "—")
    table.add_row("Operadora (NumVerify)", result.numverify_carrier or "—")
    table.add_row(
        "Tipo de linea",
        result.abstract_line_type
        if result.abstract_line_type not in ("", None, "unknown", "UNKNOWN")
        else result.numverify_line_type
        if result.numverify_line_type not in ("", None, "unknown", "UNKNOWN")
        else result.local_line_type or "—",
    )
    _console.print()
    _console.print(table)


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
    print(
        f"    Tipo de linea:       "
        f"{result.abstract_line_type or result.numverify_line_type or '—'}"
    )


def rich_print_api_results(result: ScanResult):
    table = Table(
        title="🌐 RESULTADOS DE APIs",
        box=box.ROUNDED,
        border_style="green",
        show_lines=True,
    )
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
            result.abstract_line_type or "—",
        )
    if result.numverify_data:
        table.add_row(
            "NumVerify",
            str(result.numverify_data.get("valid", "N/A")),
            result.numverify_location or "—",
            result.numverify_carrier or "—",
            result.numverify_line_type or "—",
        )
    if result.ipqualityscore_data:
        table.add_row(
            "IPQualityScore",
            str(result.ipqualityscore_data.get("valid", "N/A")),
            result.ipqualityscore_data.get("city") or "—",
            result.ipqualityscore_data.get("carrier") or "—",
            result.ipqualityscore_data.get("line_type") or "—",
        )
    _console.print()
    _console.print(table)


def plain_print_api_results(result: ScanResult):
    print("\n[+] RESULTADOS DE APIs:")
    print("-" * 60)
    if result.abstract_data:
        print(
            f"    [AbstractAPI] Valido: {result.abstract_data.get('valid', 'N/A')}, "
            f"Ubicacion: {result.abstract_location or '—'}, "
            f"Operadora: {result.abstract_carrier or '—'}, "
            f"Tipo: {result.abstract_line_type or '—'}"
        )
    if result.numverify_data:
        print(
            f"    [NumVerify]   Valido: {result.numverify_data.get('valid', 'N/A')}, "
            f"Ubicacion: {result.numverify_location or '—'}, "
            f"Operadora: {result.numverify_carrier or '—'}, "
            f"Tipo: {result.numverify_line_type or '—'}"
        )
    if result.ipqualityscore_data:
        print(
            f"    [IPQualityScore] Valido: "
            f"{result.ipqualityscore_data.get('valid', 'N/A')}, "
            f"Activo: {result.ipqualityscore_data.get('active', 'N/A')}, "
            f"Riesgo: {result.ipqualityscore_data.get('risk_score', 'N/A')}, "
            f"Abuso reciente: "
            f"{result.ipqualityscore_data.get('abuse_recent', 'N/A')}"
        )


def rich_print_provider_states(result: ScanResult):
    if not result.provider_states:
        return
    display_names = {
        "abstract_phone_intelligence": "AbstractAPI",
        "numverify": "NumVerify",
        "opencage": "OpenCage",
        "geoapify": "Geoapify",
        "ipqualityscore": "IPQualityScore",
        "nominatim": "Nominatim",
    }
    table = Table(
        title="🩺 ESTADO DE PROVEEDORES",
        box=box.ROUNDED,
        border_style="yellow",
        show_lines=True,
    )
    table.add_column("Proveedor", style="bold white", width=18)
    table.add_column("Estado", width=24)
    table.add_column("Fuente", width=14)
    table.add_column("Transporte", width=14)
    table.add_column("Detalle", width=36)
    for service, status in result.provider_states.items():
        table.add_row(
            display_names.get(service, service),
            str(status.state),
            status.source or "—",
            status.transport,
            status.detail[:80] if status.detail else "—",
        )
    _console.print()
    _console.print(table)


def plain_print_provider_states(result: ScanResult):
    if not result.provider_states:
        return
    display_names = {
        "abstract_phone_intelligence": "AbstractAPI",
        "numverify": "NumVerify",
        "opencage": "OpenCage",
        "geoapify": "Geoapify",
        "ipqualityscore": "IPQualityScore",
        "nominatim": "Nominatim",
    }
    print("\n[+] ESTADO DE PROVEEDORES:")
    print("-" * 60)
    for service, status in result.provider_states.items():
        detail = f" detail={status.detail[:80]}" if status.detail else ""
        print(
            f"    {display_names.get(service, service):18} "
            f"{str(status.state):24} source={status.source or '—'} "
            f"transport={status.transport}{detail}"
        )


def rich_print_errors(result: ScanResult):
    if not result.errors:
        return
    table = Table(
        title="⚠️ ERRORES DE PROVEEDORES",
        box=box.ROUNDED,
        border_style="red",
        show_lines=True,
    )
    table.add_column("Error", style="bold white")
    for error in result.errors:
        table.add_row(str(error))
    _console.print()
    _console.print(table)


def plain_print_errors(result: ScanResult):
    if not result.errors:
        return
    print("\n[+] ERRORES DE PROVEEDORES:")
    print("-" * 60)
    for error in result.errors:
        print(f"    {error}")


def rich_print_consensus(result: ScanResult):
    if not result.all_votes:
        return
    table = Table(
        title="🗳️  EVIDENCIA DE LOCALIDAD",
        box=box.ROUNDED,
        border_style="cyan",
        show_lines=True,
    )
    table.add_column("Fuente", style="bold white", width=20)
    table.add_column("Ciudad / Region", style="green", width=30)
    for vote in result.all_votes:
        table.add_row(vote.source, vote.city)
    table.add_row(
        "[bold green]ESTADO[/bold green]",
        f"[bold green]{result.evidence_state}[/bold green]",
    )
    table.add_row(
        "[bold green]LOCALIDAD[/bold green]",
        f"[bold green]{result.consensus_city or '—'}[/bold green]",
    )
    _console.print()
    _console.print(table)


def plain_print_consensus(result: ScanResult):
    if not result.all_votes:
        return
    print("\n[+] EVIDENCIA DE LOCALIDAD:")
    print("-" * 60)
    for vote in result.all_votes:
        print(f"    {vote.source:18} {vote.city}")
    print(f"    Estado:         {result.evidence_state}")
    print(f"    Localidad base: {result.consensus_city or '—'}")


def rich_print_geo(result: ScanResult):
    table = Table(
        title="🗺️  GEOLOCALIZACION APROXIMADA",
        box=box.ROUNDED,
        border_style="magenta",
        show_lines=True,
    )
    table.add_column("Campo", style="bold yellow", width=28)
    table.add_column("Valor", style="bold white", width=50)
    table.add_row("Localidad base", result.consensus_city or "—")
    table.add_row("Fuente geocodificacion", result.geocoding_source or "—")
    table.add_row("Latitud", f"{result.latitude:.5f}" if result.latitude else "—")
    table.add_row("Longitud", f"{result.longitude:.5f}" if result.longitude else "—")
    table.add_row(
        "OpenCage lat/lon",
        f"{result.opencage_latitude:.5f}, {result.opencage_longitude:.5f}"
        if result.opencage_latitude and result.opencage_longitude
        else "—",
    )
    table.add_row(
        "OpenCage address",
        (result.opencage_address[:70] + "...")
        if result.opencage_address
        else "—",
    )
    table.add_row(
        "Geoapify lat/lon",
        f"{result.geoapify_latitude:.5f}, {result.geoapify_longitude:.5f}"
        if result.geoapify_latitude and result.geoapify_longitude
        else "—",
    )
    table.add_row(
        "Geoapify address",
        (result.geoapify_address[:70] + "...")
        if result.geoapify_address
        else "—",
    )
    table.add_row(
        "Direccion (Nominatim)",
        (result.nominatim_address[:70] + "...")
        if result.nominatim_address
        else "—",
    )
    _console.print()
    _console.print(table)
    _console.print(
        "[dim]Nota: localidad de numeracion; NO GPS en tiempo real ni "
        "ubicacion del suscriptor.[/dim]"
    )


def plain_print_geo(result: ScanResult):
    print("\n[+] GEOLOCALIZACION APROXIMADA:")
    print("-" * 60)
    print(f"    Localidad base:  {result.consensus_city or '—'}")
    print(f"    Fuente geocodificacion: {result.geocoding_source or '—'}")
    print(
        f"    Latitud:         {result.latitude:.5f}"
        if result.latitude
        else "    Latitud:         —"
    )
    print(
        f"    Longitud:        {result.longitude:.5f}"
        if result.longitude
        else "    Longitud:        —"
    )
    if result.opencage_latitude and result.opencage_longitude:
        print(
            f"    OpenCage lat/lon: {result.opencage_latitude:.5f}, "
            f"{result.opencage_longitude:.5f}"
        )
    if result.opencage_address:
        print(f"    OpenCage address: {result.opencage_address[:70]}")
    if result.geoapify_latitude and result.geoapify_longitude:
        print(
            f"    Geoapify lat/lon: {result.geoapify_latitude:.5f}, "
            f"{result.geoapify_longitude:.5f}"
        )
    if result.geoapify_address:
        print(f"    Geoapify address: {result.geoapify_address[:70]}")
    if result.nominatim_address:
        print(f"    Direccion (Nominatim): {result.nominatim_address[:70]}")
    print(
        "    Nota: localidad de numeracion; NO GPS en tiempo real ni "
        "ubicacion del suscriptor."
    )


def rich_print_osint_links(links: dict):
    table = Table(
        title="🔗 ENLACES DE INVESTIGACION (OSINT)",
        box=box.ROUNDED,
        border_style="blue",
        show_lines=True,
    )
    table.add_column("Plataforma", style="bold white", width=22)
    table.add_column("URL", style="cyan")
    for name, url in links.items():
        table.add_row(name, url)
    _console.print()
    _console.print(table)


def plain_print_osint_links(links: dict):
    print("\n[+] ENLACES DE INVESTIGACION (OSINT):")
    print("-" * 60)
    for name, url in links.items():
        print(f"    {name:22} {url}")


def rich_print_report(result: ScanResult):
    table = Table(
        title="📁 REPORTE EXPORTADO",
        box=box.ROUNDED,
        border_style="yellow",
        show_lines=True,
    )
    table.add_column("Campo", style="bold yellow", width=28)
    table.add_column("Valor", style="bold white", width=50)
    table.add_row("Reporte JSON", result.report_path or "—")
    table.add_row("Mapa HTML", result.map_path or "—")
    table.add_row("Hash SHA-256", result.report_hash or "—")
    _console.print()
    _console.print(table)


def plain_print_report(result: ScanResult):
    print("\n[+] REPORTE EXPORTADO:")
    print("-" * 60)
    print(f"    Reporte JSON: {result.report_path or '—'}")
    print(f"    Mapa HTML:    {result.map_path or '—'}")
    print(f"    Hash SHA-256: {result.report_hash or '—'}")


def _section_break():
    if RICH_AVAILABLE:
        _console.print(Rule(style="dim"))
    else:
        print("─" * 60)


def print_results(result: ScanResult):
    _rich_or_plain(
        lambda: rich_print_subscriber(result),
        lambda: plain_print_subscriber(result),
    )
    _section_break()
    _rich_or_plain(
        lambda: rich_print_osint_links(result.osint_links),
        lambda: plain_print_osint_links(result.osint_links),
    )
    _section_break()
    _rich_or_plain(
        lambda: rich_print_api_results(result),
        lambda: plain_print_api_results(result),
    )
    _section_break()
    _rich_or_plain(
        lambda: rich_print_provider_states(result),
        lambda: plain_print_provider_states(result),
    )
    _rich_or_plain(
        lambda: rich_print_errors(result),
        lambda: plain_print_errors(result),
    )
    _section_break()
    _rich_or_plain(
        lambda: rich_print_consensus(result),
        lambda: plain_print_consensus(result),
    )
    if result.consensus_city:
        _section_break()
        _rich_or_plain(
            lambda: rich_print_geo(result),
            lambda: plain_print_geo(result),
        )
    _section_break()
    _rich_or_plain(
        lambda: rich_print_report(result),
        lambda: plain_print_report(result),
    )
    print(
        "\n[!] Ubicacion = prefijo de numeracion, "
        "NO ubicacion GPS del telefono."
    )
