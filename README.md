<p align="center">
  <img src="mexsint.png" alt="MeXiCOSINT Banner" width="850">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Licencia-MIT-green.svg" alt="Licencia">
  <img src="https://img.shields.io/badge/OSINT-México-red.svg" alt="OSINT México">
  <img src="https://img.shields.io/badge/Estado-Beta-orange.svg" alt="Estado Beta">
</p>

<h1 align="center">MeXiCOSINT</h1>

<p align="center">
  Herramienta OSINT enfocada en análisis, validación, enriquecimiento y reportes de números telefónicos mexicanos.
</p>

---

## Descripción

**MeXiCOSINT** es una herramienta de OSINT desarrollada en Python y enfocada en números telefónicos mexicanos.

La herramienta puede validar números, analizar formatos mexicanos, consultar fuentes opcionales mediante API, procesar metadatos disponibles y generar resultados útiles para investigación autorizada.

> Este proyecto está en fase beta. Los resultados deben tratarse como indicadores OSINT, no como evidencia absoluta.

---

## Características

- Validación de números telefónicos mexicanos
- Formato nacional e internacional
- Análisis local de números mexicanos
- Enriquecimiento opcional mediante APIs externas
- Procesamiento relacionado con IFT/SNS
- Soporte para módulo QuienHabla.mx
- CLI instalable con el comando `mexicosint`
- Configuración local de API keys
- Soporte para reportes o salidas generadas según la versión

---

## Estructura del repositorio

```text
MeXiCOSINT/
├── docs/
│   ├── INSTALL.md
│   ├── USAGE.md
│   └── CONFIG.md
├── src/
│   └── mexicosint/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py
│       ├── main.py
│       ├── data/
│       ├── modules/
│       │   ├── ift_sns.py
│       │   ├── local_parser.py
│       │   └── quienhabla.py
│       ├── services/
│       │   ├── ip_geo.py
│       │   └── scanner.py
│       └── utils/
│           └── validation.py
├── pyproject.toml
├── requirements.txt
├── MIGRATION.md
├── .gitignore
├── LICENSE
└── README.md
```

---

## Instalación

Clona el repositorio:

```bash
git clone https://github.com/KiMiGuel/MeXiCOSINT.git
cd MeXiCOSINT
```

Crea y activa un entorno virtual:

```bash
python3 -m venv venv
source venv/bin/activate
```

Instala el paquete en modo editable:

```bash
pip install -e .
```

También puedes instalar las dependencias explícitas para desarrollo:

```bash
pip install -r requirements.txt
```

---

## Uso

Ejecuta MeXiCOSINT con el comando instalado:

```bash
mexicosint --number 5512345678
mexicosint --number +525512345678
mexicosint -b --number 5512345678
```

El número posicional se mantiene por compatibilidad:

```bash
mexicosint 5512345678
```

Modo IP directo:

```bash
mexicosint --ip 8.8.8.8
```

Ejecutar sin instalar el comando global:

```bash
PYTHONPATH=src python3 -m mexicosint --number 5512345678
```

Usa `-b`, `--compact-banner` o el alias heredado `--small-banner` para forzar el banner compacto.

---

## Documentación

| Guía | Descripción |
|---|---|
| [Guía de instalación](docs/INSTALL.md) | Instrucciones de instalación para Kali, Debian, Ubuntu y sistemas similares |
| [Guía de uso](docs/USAGE.md) | Uso básico y notas de ejecución |
| [Guía de configuración](docs/CONFIG.md) | Configuración local y manejo de API keys |
| [Migración](MIGRATION.md) | Cambios de estructura para el paquete instalable |

---

## APIs opcionales

Algunas funciones pueden depender de API keys externas.

| Servicio | Función |
|---|---|
| AbstractAPI | Validación y enriquecimiento de números telefónicos |
| NumVerify | Validación secundaria de números |
| Shodan | Enriquecimiento opcional relacionado con servicios expuestos |
| IPInfo | Enriquecimiento de metadatos IP |
| IP2Location | Enriquecimiento de metadatos IP |
| OpenCage | Geocodificación y soporte para mapas |

Las API keys deben mantenerse en tu entorno local. No las subas a GitHub.

---

## Seguridad

No subas archivos como:

```text
.env
*.env
config.json
secrets.json
keys.json
tokens.json
credentials.json
*.local.json
*.config.json
.mx_osint_config.json
```

Ruta local recomendada para configuración:

```text
~/.mx_osint_config.json
```

Permisos recomendados:

```bash
chmod 600 ~/.mx_osint_config.json
```

---

## Advertencia

**MeXiCOSINT** está diseñado para investigación autorizada, autoauditoría y flujos educativos de OSINT.

No uses esta herramienta para acoso, doxxing, fraude, amenazas o actividades no autorizadas.

La herramienta no garantiza identidad, ubicación exacta, propiedad ni atribución definitiva de un número telefónico.

---

## Estado del proyecto

Este proyecto está en desarrollo activo.

Funciones planeadas:

- Publicación de releases en GitHub
- Paquete `.deb` para instalación local con `apt`
- Mejoras en documentación
- Más pruebas y validaciones internas

---

## Licencia

Este proyecto se publica bajo la licencia incluida en este repositorio.
