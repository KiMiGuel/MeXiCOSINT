# Instrucciones de migración

MeXiCOSINT usa una estructura de paquete `src/` lista para distribución.

## Qué cambió

- `mexicosint_v2.2.5.py` fue reemplazado por `src/mexicosint/main.py`.
- El punto de entrada de la CLI ahora vive en `src/mexicosint/cli.py`.
- Los módulos auxiliares se movieron de `modules/` a `src/mexicosint/modules/`.
- Los wrappers de servicios viven en `src/mexicosint/services/`.
- Los helpers compartidos viven en `src/mexicosint/utils/`.
- La metadata del paquete y el script de consola se definen en `pyproject.toml`.
- Los datos locales IFT/LADA viven en `src/mexicosint/data/` para incluirse en el paquete.

## Instalación para desarrollo

```bash
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

## Ejecutar después de la migración

Usa el comando instalado:

```bash
mexicosint 5512345678
mexicosint --dummy-test 6634647308
mexicosint -b 5512345678
```

Ejecutar sin instalar:

```bash
PYTHONPATH=src python3 -m mexicosint 5512345678
```

O usar el launcher del repositorio:

```bash
bash bin/mexicosint 5512345678
```

## Cambios de imports

Usa imports absolutos del paquete:

```python
from mexicosint.modules.local_parser import parse_mx_number
from mexicosint.modules.ift_sns import consultar
from mexicosint.modules.quienhabla import consultar as consultar_quienhabla
from mexicosint.services.scanner import run_phone_scan
```
