<p align="center">
  <img src="mexsint.png" alt="MeXiCOSINT Banner" width="850">
</p>

<p align="center">
  <img src="https://img.shields.io/pypi/v/mexicosint.svg" alt="PyPI">
  <img src="https://img.shields.io/github/v/release/KiMiGuel/MeXiCOSINT.svg" alt="Release">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Licencia-MIT-green.svg" alt="Licencia">
  <img src="https://img.shields.io/badge/OSINT-México-red.svg" alt="OSINT México">
  <img src="https://img.shields.io/badge/Estado-Beta-orange.svg" alt="Estado Beta">
</p>

<h1 align="center">MeXiCOSINT 📞🔍</h1>

<p align="center">
  Herramienta OSINT enfocada en análisis, validación, enriquecimiento y reportes de números telefónicos mexicanos.
</p>

---

## Descripción 🧭

**MeXiCOSINT** es una herramienta de OSINT desarrollada en Python y enfocada en números telefónicos mexicanos.

La herramienta puede validar números, analizar formatos mexicanos, consultar fuentes opcionales mediante API, procesar metadatos disponibles y generar resultados útiles para investigación autor[...]

> Este proyecto está en fase beta. Los resultados deben tratarse como indicadores OSINT, no como evidencia absoluta.

---

## Características ✨

- Validación de números telefónicos mexicanos
- Formato nacional e internacional
- Análisis local de números mexicanos
- Enriquecimiento opcional mediante APIs externas
- Procesamiento relacionado con IFT/SNS
- Soporte para módulo QuienHabla.mx
- **Base oficial IFT/PNN integrada**: 177k+ bloques de numeración asignada, consulta offline
- Operadora, modalidad y fecha de asignación directo del regulador
- Localidad canónica IFT/LADA: bloque IFT exacto como fuente primaria y LADA como respaldo o apoyo
- Series no geográficas 200/300/500/800/900 con alerta de números premium (900)
- Gestión de API keys desde la CLI (`--set-key`, `--list-keys`, `--config-path`)
- Configuración local de API keys
- Soporte para reportes o salidas generadas según la versión
- Modo telefónico únicamente: sin proveedores IP ni escaneo IP

---

## Estructura del repositorio 📂

```text
MeXiCOSINT/
├── bin/
│   └── mexicosint
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
│       │   ├── ift_blocks.py
│       │   ├── ift_sns.py
│       │   ├── local_parser.py
│       │   └── quienhabla.py
│       ├── services/
│       │   └── scanner.py
│       └── utils/
│           └── validation.py
├── tools/
│   └── update_ift_blocks.py
├── pyproject.toml
├── requirements.txt
├── .gitignore
├── LICENSE
└── README.md
```

---

## Instalación ⚙️

### Opción 1: pipx (recomendada)

MeXiCOSINT está publicado en PyPI. La forma recomendada de instalarlo es con `pipx`, que instala el comando de forma global pero aislada, sin tocar el Python del sistema (importante en Kali Linux[...]

```bash
sudo apt install -y pipx
pipx install mexicosint
```

Después solo ejecuta:

```bash
mexicosint
```

Para actualizar a una nueva versión:

```bash
pipx upgrade mexicosint
```

### Opción 2: pip directo

Si prefieres pip (fuera de Kali, o usando `--break-system-packages` en Kali):

```bash
pip install mexicosint
```

### Opción 3: clonar el repositorio

Útil si quieres modificar el código o colaborar:

```bash
git clone https://github.com/KiMiGuel/MeXiCOSINT.git
cd MeXiCOSINT
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

### Actualizar la base IFT (opcional)

El paquete ya incluye la base. Para actualizarla con el plan vigente del IFT:

```bash
python3 tools/update_ift_blocks.py
```

---

## Uso ▶️

Ejecuta MeXiCOSINT usando el comando:

```bash
mexicosint 5512345678
mexicosint -b 5512345678
```

Gestión de API keys desde la CLI:

```bash
mexicosint --set-key opencage TU_KEY
mexicosint --set-key geoapify TU_KEY
mexicosint --set-key google_places TU_KEY
mexicosint --set-key ipqualityscore TU_KEY
mexicosint --set-key abstract TU_KEY
mexicosint --set-key numverify TU_KEY
mexicosint --list-keys
mexicosint --config-path
```

Si clonaste el repositorio, también puedes usar el launcher sin instalar el comando global:

```bash
bash bin/mexicosint 5512345678
```

O ejecutar el módulo del paquete:

```bash
PYTHONPATH=src python3 -m mexicosint 5512345678
```

Usa `-b`, `--compact-banner` o el alias heredado `--small-banner` para forzar el banner ASCII compacto.

---

## Documentación 📚

| Guía | Descripción |
|---|---|
| [Guía de instalación](docs/INSTALL.md) | Instrucciones de instalación para Kali, Debian, Ubuntu y sistemas similares |
| [Guía de uso](docs/USAGE.md) | Uso completo: opciones, ejemplos, base IFT, API keys |
| [Guía de configuración](docs/CONFIG.md) | Configuración local y manejo de API keys |
| [Documentación en inglés](docs/ENGLISH.md) | Documentación completa en inglés |

---

## APIs opcionales 🔗

Algunas funciones pueden depender de API keys externas.

| Servicio | Función |
|---|---|
| AbstractAPI | Validación y enriquecimiento telefónico como evidencia de apoyo |
| NumVerify | Validación secundaria como evidencia de apoyo |
| OpenCage | Geocodificación primaria opcional de localidad IFT/LADA |
| Geoapify | Geocodificación fallback opcional de localidad IFT/LADA |
| Google Places | Posibles fichas públicas de negocio por número E.164, sin atribución de suscriptor |
| IPQualityScore | Validación, reputación y abuso telefónico como evidencia de apoyo |

Formatos aceptados: `+526634647308`, `526634647308`, `6634647308`, `+52 663 464 7308`, `52-663-464-7308`, `(663) 464-7308`.

La localidad se arma desde IFT/LADA como `<ciudad o municipio>, <estado>, Mexico`. Los valores vagos de APIs externas, como país, región o etiquetas genéricas, no se geocodifican ni reemplazan[...]

Los proveedores se usan automáticamente cuando su key existe; si falta una key, esa fuente se omite sin detener el análisis. `--dummy-test` usa fixtures y no realiza llamadas reales a APIs.

Las API keys deben mantenerse en tu entorno local. No las subas a GitHub.

---

## Seguridad 🔒

No subas archivos como:

```text
.env
*.env
config.json
secrets.json
keys.json
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

## Advertencia ⚠️

**MeXiCOSINT** está diseñado para investigación autorizada, autoauditoría y flujos educativos de OSINT.

No uses esta herramienta para acoso, doxxing, fraude, amenazas o actividades no autorizadas.

La herramienta no garantiza identidad, ubicación exacta, propiedad ni atribución definitiva de un número telefónico.

---

## Estado del proyecto 🚧

Este proyecto está en desarrollo activo.

Funciones planeadas:

- Publicación de releases en GitHub
- Paquete `.deb` para instalación local con `apt`
- Mejoras en documentación
- Más pruebas y validaciones internas

---

## Licencia 📜

Este proyecto se publica bajo la licencia incluida en este repositorio.
