# Migration Instructions

MeXiCOSINT now uses a production-style `src/` package layout.

## What changed

- `mexicosint_v2.2.5.py` was replaced by `src/mexicosint/main.py`.
- The command-line entry point is now `src/mexicosint/cli.py`.
- Existing helper modules moved from `modules/` to `src/mexicosint/modules/`.
- Service-facing wrappers live in `src/mexicosint/services/`.
- Shared helpers live in `src/mexicosint/utils/`.
- Package metadata and the console script are defined in `pyproject.toml`.
- Local IFT data moved into `src/mexicosint/data/` so it can be packaged.

## Install for development

```bash
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

## Run after migration

Use the installed command:

```bash
mexicosint 5512345678
mexicosint --ip 8.8.8.8
mexicosint --dummy-test 5512345678
mexicosint -b 5512345678
```

Run without installing:

```bash
PYTHONPATH=src python3 -m mexicosint 5512345678
```

Or use the repository launcher:

```bash
bash bin/mexicosint 5512345678
```

## Import changes

Use absolute package imports:

```python
from mexicosint.modules.local_parser import parse_mx_number
from mexicosint.modules.ift_sns import consultar
from mexicosint.modules.quienhabla import consultar as consultar_quienhabla
from mexicosint.services.scanner import run_phone_scan
```
