"""Command-line interface for MeXiCOSINT."""

from __future__ import annotations

import argparse

from mexicosint import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mexicosint",
        description="OSINT para numeros telefonicos Mexicanos.",
    )
    parser.add_argument(
        "number",
        nargs="?",
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
        "--set-key",
        nargs=2,
        metavar=("SERVICIO", "KEY"),
        help="Guarda una API key en el archivo de configuracion (ej. --set-key opencage TU_KEY).",
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
    )
    return parser


def _to_legacy_argv(args: argparse.Namespace) -> list[str]:
    """Translate argparse output to the existing scanner argument format."""
    argv: list[str] = []
    if args.dummy_test:
        argv.append("--dummy-test")
    if args.small_banner:
        argv.append("--small-banner")
    if args.ip:
        argv.extend(["--ip", args.ip])
    elif args.number:
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

    if not args.ip and not args.number:
        parser.print_help()
        return 1

    from mexicosint import main as app

    app.main(_to_legacy_argv(args))
    return 0
