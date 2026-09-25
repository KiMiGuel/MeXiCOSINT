"""Command-line interface for MeXiCOSINT."""

from __future__ import annotations

import argparse

from mexicosint import __version__

EPILOG = """ejemplos:
  mexicosint 5512345678                  Escanea un numero mexicano (MicroVault se detecta solo)
  mexicosint +525512345678               Formato internacional tambien funciona

  credenciales:
    Solo se leen del perfil MicroVault 'mexicosint' mediante el bridge local.
    MeXiCOSINT no lee variables de entorno genericas ni archivos JSON.
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mexicosint",
        description="OSINT para numeros telefonicos Mexicanos.",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,
    )
    parser.add_argument(
        "-h",
        "--help",
        action="help",
        help="Muestra esta ayuda y sale.",
    )
    parser.add_argument(
        "number",
        nargs="?",
        help="Numero telefonico mexicano a escanear.",
    )
    parser.add_argument(
        "--dummy-test",
        action="store_true",
        help=argparse.SUPPRESS,  # internal debugging only, not documented publicly
    )
    parser.add_argument(
        "--microvault",
        action="store_true",
        help="Fuerza la conexion a MicroVault (ya se detecta solo si esta instalado).",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Muestra la version instalada y sale.",
    )
    return parser


def _to_legacy_argv(args: argparse.Namespace) -> list[str]:
    """Translate argparse output to the scanner argument format.

    Number goes first for the scanner entrypoint.
    """
    argv: list[str] = []
    if args.dummy_test:
        argv.append("--dummy-test")
    if args.microvault:
        argv.append("--microvault")
    if args.number:
        argv.append(args.number)
    return argv


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.number:
        parser.print_help()
        return 1

    from mexicosint import main as app

    app.main(_to_legacy_argv(args))
    return 0
