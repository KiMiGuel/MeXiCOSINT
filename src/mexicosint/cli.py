"""Command-line interface for MeXiCOSINT."""

from __future__ import annotations

import argparse

from mexicosint import __version__

EPILOG = """ejemplos:
  mexicosint 5512345678                  Escanea un numero mexicano (MicroVault se detecta solo)
  mexicosint +525512345678               Formato internacional tambien funciona
  mexicosint --no-microvault 5512345678  Omite MicroVault aunque este instalado
  mexicosint --set-key geoapify TU_KEY   Guarda una API key
  mexicosint --list-keys                 Muestra keys guardadas (enmascaradas)
  mexicosint --config-path               Ruta del archivo de configuracion

fuentes de API keys (en orden de prioridad):
  1. Variables de entorno   MEXICOSINT_GEOAPIFY_API_KEY, etc.
  2. MicroVault             auto-detectado (vault cifrado en ~/.microvault/);
                            --no-microvault lo omite, --microvault lo fuerza
  3. Archivo JSON           ~/.mx_osint_config.json (opcional)

servicios validos para --set-key:
  abstract (alias de abstract_phone_intelligence), numverify,
  opencage, geoapify, ipqualityscore
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
        "--no-microvault",
        action="store_true",
        help="Omite MicroVault aunque este instalado (no pide contraseña).",
    )
    parser.add_argument(
        "--set-key",
        nargs=2,
        metavar=("SERVICIO", "KEY"),
        help="Guarda una API key en el archivo de configuracion.",
    )
    parser.add_argument(
        "--list-keys",
        action="store_true",
        help="Muestra las API keys configuradas (enmascaradas) y sale.",
    )
    parser.add_argument(
        "--config-path",
        action="store_true",
        help="Muestra la ruta del archivo de configuracion y sale.",
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
    if args.no_microvault:
        argv.append("--no-microvault")
    if args.number:
        argv.append(args.number)
    return argv


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.config_path:
        from mexicosint.main import CONFIG_PATH
        print(CONFIG_PATH)
        return 0

    if args.list_keys:
        from mexicosint.main import list_keys_cli
        return list_keys_cli()

    if args.set_key:
        from mexicosint.main import set_key_cli
        return set_key_cli(args.set_key[0], args.set_key[1])

    if not args.number:
        parser.print_help()
        return 1

    from mexicosint import main as app

    app.main(_to_legacy_argv(args))
    return 0
