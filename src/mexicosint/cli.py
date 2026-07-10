"""Command-line interface for MeXiCOSINT."""

from __future__ import annotations

import argparse
from typing import List, Optional

from mexicosint import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mexicosint",
        description="OSINT para numeros telefonicos Mexicanos.",
    )
    parser.add_argument(
        "number",
        nargs="?",
        help="Numero telefonico mexicano a escanear. Se mantiene por compatibilidad.",
    )
    parser.add_argument(
        "--number",
        dest="phone_number",
        metavar="PHONE",
        help="Numero telefonico mexicano a escanear.",
    )
    parser.add_argument(
        "--ip",
        dest="ip",
        metavar="ADDRESS",
        help="Geolocaliza directamente una direccion IP.",
    )
    parser.add_argument(
        "--dummy-test",
        action="store_true",
        help="Usa datos de prueba y evita llamadas reales a APIs.",
    )
    parser.add_argument(
        "-b",
        "--compact-banner",
        "--small-banner",
        dest="small_banner",
        action="store_true",
        help="Fuerza el banner compacto; alias: --small-banner.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def _scan_number(args: argparse.Namespace) -> Optional[str]:
    return args.phone_number or args.number


def _to_scanner_argv(args: argparse.Namespace) -> List[str]:
    """Translate CLI options to the scanner argument format."""
    argv = []
    if args.dummy_test:
        argv.append("--dummy-test")
    if args.small_banner:
        argv.append("--small-banner")
    if args.ip:
        argv.extend(["--ip", args.ip])
    else:
        number = _scan_number(args)
        if number:
            argv.append(number)
    return argv


def run(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.ip and _scan_number(args):
        parser.error("usa --ip o --number, no ambos")

    if not args.ip and not _scan_number(args):
        parser.print_help()
        return 1

    from mexicosint import main as app

    app.main(_to_scanner_argv(args))
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    """Backward-compatible wrapper for older entry-point references."""
    return run(argv)
