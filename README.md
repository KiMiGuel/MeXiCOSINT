<p align="center">
  <img src="mexsint.png" alt="MeXiCOSINT Banner" width="850">
</p>

<p align="center">
  <img src="https://img.shields.io/pypi/v/mexicosint.svg" alt="PyPI">
  <img src="https://img.shields.io/github/v/release/KiMiGuel/MeXiCOSINT.svg" alt="Release">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Licencia-MIT-green.svg" alt="Licencia">
  <img src="https://img.shields.io/badge/OSINT-México-red.svg" alt="OSINT México">
  <img src="https://img.shields.io/badge/Estado-Beta-brightgreen.svg" alt="Estado Beta">
</p>

<h1 align="center">MeXiCOSINT 📞🔍</h1>

<p align="center">
  Herramienta OSINT enfocada en análisis, validación, enriquecimiento y reportes de números telefónicos mexicanos.
</p>

---

<p align="center">
  <img src="docs/brag.gif" alt="MeXiCOSINT demo" width="850">
</p>

---

## Descripción 🧭

**MeXiCOSINT** es una herramienta de OSINT desarrollada en Python y enfocada en números telefónicos mexicanos.

La herramienta puede validar números, analizar formatos mexicanos, consultar fuentes opcionales mediante API, procesar metadatos disponibles y generar resultados útiles para investigación autorizada.

> Este proyecto está en fase beta. Los resultados deben tratarse como indicadores OSINT, no como evidencia absoluta.

---

## Características ✨

- Validación de números telefónicos mexicanos
- Formato nacional e internacional
- Análisis local de números mexicanos
- Enriquecimiento opcional mediante APIs externas
- Procesamiento relacionado con IFT/SNS
- Búsquedas OSINT mediante enlaces públicos para WhatsApp y redes sociales
- **Base oficial IFT/PNN integrada**: 177k+ bloques de numeración asignada, consulta offline
- Operadora, modalidad y fecha de asignación directo del regulador
- Localidad canónica IFT/LADA: bloque IFT exacto como fuente primaria y LADA como respaldo o apoyo
- Series no geográficas 200/300/500/800/900 con alerta de números premium (900)
- Estado estructurado por proveedor: `missing`, `not_requested`, `configured_unverified`, `request_success`, `no_result`, `auth_failed`, `quota_exceeded` y más
- Fuente de geocodificación seleccionada visible en el resultado
- **MicroVault como único backend de credenciales** para el enriquecimiento normal; se requiere el perfil `mexicosint`
- **Modelo Mexico-first (v2.8.0)**: IFT/PNN es la fuente primaria para bloques de numeración mexicanos; Abstract, NumVerify e IPQualityScore se muestran como corroboración secundaria y no reemplazan los datos oficiales
- **Matriz de confianza**: el reporte identifica qué campos provienen de IFT/PNN y cuáles son señales secundarias
- **Rendimiento concurrente (v2.5.3)**: llamadas a APIs en paralelo (asyncio + aiohttp), pooling de conexiones HTTPS y memoización de normalización y geocodificación
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
│   ├── CONFIG.md
│   ├── ENGLISH.md
│   └── index.html
├── src/
│   └── mexicosint/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py
│       ├── config.py
│       ├── evidence.py
│       ├── locality.py
│       ├── main.py
│       ├── microvault_bridge.py
│       ├── numbering.py
│       ├── presentation.py
│       ├── reporting.py
│       ├── core/
│       │   ├── models.py
│       │   ├── scan_result.py
│       │   └── settings.py
│       ├── data/
│       │   ├── lada.py
│       │   ├── ift_blocks.csv.gz
│       │   └── ift_ng_blocks.csv.gz
│       ├── modules/
│       │   ├── ift_blocks.py
│       │   └── local_parser.py
│       ├── providers/
│       │   ├── abstract.py
│       │   ├── base.py
│       │   ├── geoapify.py
│       │   ├── ipqualityscore.py
│       │   ├── models.py
│       │   ├── nominatim.py
│       │   ├── numverify.py
│       │   ├── opencage.py
│       │   └── status.py
│       └── services/
│           └── scanner.py
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

MeXiCOSINT está publicado en PyPI. La forma recomendada de instalarlo es con `pipx`, que instala el comando de forma global pero aislada, sin tocar el Python del sistema (importante en Kali Linux).

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
mexicosint +525512345678
mexicosint --mexico-only 5512345678
mexicosint --batch numeros.txt
mexicosint --diff antes.json despues.json
```

`--mexico-only` omite AbstractAPI, NumVerify e IPQualityScore, conservando
IFT/PNN y la geolocalización aproximada de localidad. `--batch` procesa un
archivo con un número por línea y genera un manifest JSON y un resumen CSV.
`--diff` compara la evidencia de dos reportes JSON.

La CLI ya no ofrece configuración de credenciales. La única fuente para
proveedores es MicroVault, mediante el perfil `mexicosint`.

Si clonaste el repositorio, también puedes usar el launcher sin instalar el comando global:

```bash
bash bin/mexicosint 5512345678
```

O ejecutar el módulo del paquete:

```bash
PYTHONPATH=src python3 -m mexicosint 5512345678
```

MicroVault se detecta y se usa automáticamente para el enriquecimiento normal.
La única fuente es el perfil `mexicosint`; `--microvault` fuerza la conexión.

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
| IPQualityScore | Validación, reputación y abuso telefónico como evidencia de apoyo |

Formatos aceptados: `+526634647308`, `526634647308`, `6634647308`, `+52 663 464 7308`, `52-663-464-7308`, `(663) 464-7308`.

La localidad se arma desde IFT/LADA como `<ciudad o municipio>, <estado>, Mexico`. Los valores vagos de APIs externas, como país, región o etiquetas genéricas, no se geocodifican ni reemplazan la localidad canónica.

Los proveedores se usan automáticamente cuando su key existe; si falta una key, esa fuente se omite sin detener el análisis.

Las API keys deben mantenerse en tu entorno local. No las subas a GitHub.

---

## Seguridad 🔒

No subas archivos que contengan credenciales o datos sensibles:

```text
.env
*.env
config.json
secrets.json
keys.json
credentials.json
```

MeXiCOSINT no crea ni lee un archivo JSON de credenciales. Las keys se
administran exclusivamente en MicroVault.

---

## Advertencia ⚠️

**MeXiCOSINT** está diseñado para investigación autorizada, autoauditoría y flujos educativos de OSINT.

No uses esta herramienta para acoso, doxxing, fraude, amenazas o actividades no autorizadas.

La herramienta no garantiza identidad, ubicación exacta, propiedad ni atribución definitiva de un número telefónico.

---

## MicroVault requerido para enriquecimiento 🔐

[MicroVault](https://github.com/KiMiGuel/MicroVault) es el backend local y
cifrado de credenciales. Los escaneos normales requieren el perfil
`mexicosint`; la CLI lo obtiene mediante:

```bash
microvault env --profile mexicosint --json
```

No se aceptan variables de entorno genéricas, JSON plano, un vault completo ni
consultas por servicio como fuente alternativa.

Instala/configura MicroVault y crea el perfil:

```bash
pip install microvault
```

### 2. Configura los servicios que quieras usar

Estos son los nombres de servicio que MeXiCOSINT reconoce para proveedores opcionales. Solo necesitas guardar los que realmente utilizarás:
```bash
microvault add geoapify
microvault add opencage_api
microvault add ipgs
microvault add numverify_api
microvault add abstract_api
```

`microvault add <nombre>` pide la key con un prompt oculto — nunca se escribe en la misma línea, nunca queda en tu historial de shell.

### 3. Agrúpalas en un perfil

Esto hace que MeXiCOSINT solo vea esas 5 keys — nunca el resto de tu bóveda, aunque tengas otros servicios guardados ahí para otras herramientas:

```bash
microvault profile mexicosint geoapify opencage_api ipgs numverify_api abstract_api verificaremails
```

### 4. Ejecuta MeXiCOSINT normalmente

```bash
mexicosint 5512345678
```

Nada más. MeXiCOSINT detecta MicroVault automáticamente. `--microvault` fuerza
la conexión y hace fallar el escaneo si el perfil no puede abrirse.

Casos especiales:

```bash
mexicosint --microvault 5512345678      # fuerza la conexion (falla si no puede)
```

Si MicroVault necesita abrir su prompt pero MeXiCOSINT se ejecuta desde una terminal no interactiva, muestra un error específico de terminal interactiva. No lo confunde con una contraseña incorrecta.

### Nombres de las keys

| Key en MicroVault | Para qué se usa |
|---|---|
| `geoapify` | Geocodificación de respaldo |
| `opencage_api` | Geocodificación primaria |
| `ipgs` | Reputación y abuso telefónico |
| `numverify_api` | Validación secundaria |
| `abstract_api` | Enriquecimiento telefónico |

Si tu bóveda usa otros nombres, puedes ajustarlos en `src/mexicosint/config.py` (variable `MICROVAULT_SERVICES`) o crear un alias en MicroVault con el comando `microvault alias`.

El bridge es estricto: consulta el perfil una vez y falla cerrado si el perfil
no existe, la respuesta es inválida o MicroVault no está disponible.

---

## Portense bien cabrones. 🚧

---

## Licencia 📜

Este proyecto se publica bajo la licencia incluida en este repositorio.
