# Migration Instructions

MeXiCOSINT now uses a production-style `src/` package layout and an installable console command.

## What changed

- The versioned script was replaced by `src/mexicosint/main.py`.
- The command-line interface lives in `src/mexicosint/cli.py`.
- The package entry point is `mexicosint = mexicosint.cli:run` in `pyproject.toml`.
- Existing helper modules live in `src/mexicosint/modules/`.
- Service-facing wrappers live in `src/mexicosint/services/`.
- Shared helpers live in `src/mexicosint/utils/`.
- Local IFT data lives in `src/mexicosint/data/` so it can be packaged.
- The legacy `bin/mexicosint` shell launcher was removed; use the installed `mexicosint` command instead.

## Install for development

```bash
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

Optional explicit dependency install for development:

```bash
pip install -r requirements.txt
```

## Run after migration

Use the installed command:

```bash
mexicosint --number 5512345678
mexicosint --number +525512345678
mexicosint --ip 8.8.8.8
mexicosint --dummy-test --number 5512345678
mexicosint -b --number 5512345678
```

The positional number form remains available for compatibility:

```bash
mexicosint 5512345678
```

Run without installing:

```bash
PYTHONPATH=src python3 -m mexicosint --number 5512345678
```

## Import changes

Use absolute package imports:

```python
from mexicosint.modules.local_parser import parse_mx_number
from mexicosint.modules.ift_sns import consultar
from mexicosint.modules.quienhabla import consultar as consultar_quienhabla
from mexicosint.services.scanner import run_phone_scan
```

## Safe migration steps

1. Create a branch before changing structure.
2. Move source files under `src/mexicosint/`.
3. Convert script execution to `src/mexicosint/cli.py` and `src/mexicosint/main.py`.
4. Configure `pyproject.toml` with the `mexicosint` console script.
5. Install with `pip install -e .` in a virtual environment.
6. Run `mexicosint --number 5512345678` and `PYTHONPATH=src python3 -m mexicosint --number 5512345678`.
7. Remove references to legacy shell launchers from docs and scripts.
