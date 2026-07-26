# Guía de uso

Esta guía explica cómo usar **MeXiCOSINT** después de instalarlo.

Para instalarlo, revisa primero:

```text
docs/INSTALL.md
```

---

## Ejecutar MeXiCOSINT

Si instalaste desde PyPI (pipx o pip):

```bash
mexicosint <numero>
```

Si clonaste el repositorio, activa el entorno virtual y usa el launcher:

```bash
cd MeXiCOSINT
source venv/bin/activate
bash bin/mexicosint <numero>
```

También puedes ejecutar el módulo directamente:

```bash
PYTHONPATH=src python3 -m mexicosint <numero>
```

---

## Formato del número

MeXiCOSINT está enfocado en números telefónicos mexicanos.

Formato internacional recomendado:

```text
+52XXXXXXXXXX
```

También acepta formato nacional de 10 dígitos:

```text
XXXXXXXXXX
```

Ejemplos:

```bash
mexicosint 5512345678
mexicosint +525512345678
mexicosint "52-663-464-7308"
mexicosint "(663) 464-7308"
```

Formatos aceptados: `+526634647308`, `526634647308`, `6634647308`, `+52 663 464 7308`, `52-663-464-7308`, `(663) 464-7308`.

---

## Todas las opciones

```text
mexicosint [-h] [--dummy-test] [-b]
           [--set-key SERVICIO KEY] [--list-keys] [--config-path]
           [--version] [number]
```

| Opción | Descripción |
|---|---|
| `number` | Número telefónico mexicano a escanear |
| `--dummy-test` | Datos de prueba, sin llamadas reales a APIs |
| `-b`, `--compact-banner` | Fuerza el banner compacto (alias: `--small-banner`) |
| `--set-key SERVICIO KEY` | Guarda una API key en el archivo de configuración |
| `--list-keys` | Muestra las API keys guardadas (enmascaradas) |
| `--config-path` | Muestra la ruta del archivo de configuración |
| `--version` | Muestra la versión instalada |
| `-h`, `--help` | Ayuda completa con ejemplos |

---

## Ejemplos

Escaneo básico:

```bash
mexicosint 5512345678
```

Prueba sin consumir créditos de API:

```bash
mexicosint --dummy-test 6634647308
```

Banner compacto:

```bash
mexicosint -b 5512345678
```

## Gestión de API keys

Ya no necesitas editar el archivo de configuración a mano.

Guardar una key:

```bash
mexicosint --set-key opencage TU_KEY
mexicosint --set-key geoapify TU_KEY
mexicosint --set-key google_places TU_KEY
mexicosint --set-key ipqualityscore TU_KEY
mexicosint --set-key abstract TU_KEY
mexicosint --set-key numverify TU_KEY
```

Servicios válidos: `abstract` (alias de `abstract_phone_intelligence`), `numverify`, `opencage`, `geoapify`, `google_places`, `ipqualityscore`.

Ver el estado de las keys (enmascaradas):

```bash
mexicosint --list-keys
```

Ver dónde está el archivo de configuración:

```bash
mexicosint --config-path
```

El archivo se crea con permisos `0o600` (solo tu usuario puede leerlo).

---

## Resultados: base oficial IFT/PNN

Desde la versión 2.5.0, MeXiCOSINT incluye la **base oficial del Plan Nacional de Numeración (IFT)** integrada — más de 177,000 bloques de numeración asignada en México, consultada **offline** (sin internet, sin API keys).

Cada escaneo puede mostrar:

| Campo | Descripción |
|---|---|
| Operadora (IFT oficial) | Concesionario dueño del bloque, directo del regulador (ej. Telcel, Telmex, AT&T) |
| Modalidad (IFT) | Línea fija, Móvil (CPP/MPP) o No geográfico |
| Asignado (IFT) | Fecha en que el bloque fue asignado al concesionario |
| Tipo de servicio (IFT) | Solo series no geográficas: 800 (cobro revertido), 900 (sobre cuota), etc. |

### Series no geográficas

Los números 200/300/500/800/900 se identifican automáticamente:

| Serie | Tipo |
|---|---|
| 200 | Telefonía satelital |
| 300 | Cobro compartido |
| 500 | Números personales |
| 800 | Cobro revertido (toll-free) |
| 900 | **Sobre cuota — alerta roja, posible estafa** |

### Actualizar la base IFT

El IFT publica nuevas asignaciones periódicamente. Para actualizar la base local (requiere el repositorio clonado):

```bash
cd MeXiCOSINT
python3 tools/update_ift_blocks.py
```

El script descarga el plan vigente desde sns.ift.org.mx y reconstruye la base. Con `--offline` reconstruye sin descargar.

---

## Resultados generales

Dependiendo de la configuración y API keys disponibles, un escaneo puede mostrar:

* Validación del número y formato E.164
* **Operadora, modalidad y fecha de asignación (IFT, offline)**
* Región (phonenumbers) y referencia LADA
* Operadora y ubicación reportadas por APIs (AbstractAPI, NumVerify, IPQualityScore) como evidencia de apoyo o conflicto
* Localidad canónica IFT/LADA con atribución clara de fuente
* Enlaces de investigación OSINT
* OpenCage, Geoapify o Nominatim para geocodificar la localidad IFT/LADA + mapa HTML
* Google Places para posibles fichas públicas de negocio buscadas por número E.164
* IPQualityScore para reputación y abuso telefónico
* Reporte JSON exportado en `output/reports/`

> Los enlaces OSINT completos también quedan guardados en el reporte JSON.

---

## Sin API keys

MeXiCOSINT funciona parcialmente sin keys:

```text
Sin API keys: validación, parsing local, base IFT completa, LADA, enlaces OSINT
Con API keys: enriquecimiento adicional, geocodificación, fichas públicas de negocio y reputación telefónica
```

La base IFT funciona siempre, con o sin keys.

---

## Localidad y geocodificación

La localidad mexicana se resuelve en este orden:

1. Normaliza el número.
2. Consulta exacta de bloque IFT.
3. Ciudad/municipio y estado canónicos desde IFT.
4. LADA solo como respaldo o evidencia de apoyo.
5. Geocodificación únicamente de una consulta concreta: `<ciudad o municipio>, <estado>, Mexico`.

AbstractAPI, NumVerify e IPQualityScore pueden aportar evidencia o conflicto, pero no reemplazan una localidad concreta de IFT/LADA. Valores vagos como `Mexico`, `NorthWest`, regiones genéricas, tipo de línea o país sin ciudad no se envían a geocodificadores.

OpenCage se usa como geocodificador primario si tiene key. Geoapify se usa como fallback con key. Nominatim queda como fallback final sin key.

Google Places busca el número E.164 normalizado directamente, con formato de búsqueda como `+52 664 483 7308`. IFT/LADA solo ayuda a validar o sesgar regionalmente una ficha pública candidata.

---

## Enlaces OSINT

Los enlaces generados usan variantes exactas del número: WhatsApp por `wa.me`, búsqueda Google del E.164, dígitos internacionales, dígitos nacionales, formato espaciado y búsquedas `site:` para Facebook, TikTok, X y Twitter.

---

## Modo de prueba

```bash
mexicosint --dummy-test 6634647308
```

Usa datos de ejemplo y no realiza llamadas reales a APIs. Pensado para desarrollo y pruebas; también valida que el flujo de proveedores pueda ejecutarse sin keys reales.

---

## Buenas prácticas

* Verifica resultados con más de una fuente.
* No trates resultados OSINT como evidencia absoluta.
* No subas API keys a GitHub.
* No publiques reportes con información sensible.
* Un número reportado como "línea fija" de un concesionario mayorista que envía SMS publicitarios es un patrón común de spam.
* Usa la herramienta únicamente en investigaciones autorizadas, autoauditoría o fines educativos.

---

## Solución rápida de problemas

### `mexicosint: command not found`

Si instalaste con pipx:

```bash
pipx ensurepath
```

Cierra y abre la terminal.

### Error de dependencias (instalación desde repo)

```bash
pip install -r requirements.txt
```

### API key no detectada

```bash
mexicosint --list-keys
```

Si falta alguna, agrégala con `--set-key`.

### No aparece la información IFT

La base IFT se incluye con el paquete. Si clonaste el repo y falta, regenera:

```bash
python3 tools/update_ift_blocks.py --offline
```

O descarga la versión vigente:

```bash
python3 tools/update_ift_blocks.py
```

---

## Estado

Si todo está correcto:

```bash
mexicosint --version
```

debería mostrar la versión instalada, y:

```bash
mexicosint 5512345678
```

debería mostrar el banner, la información del número y la operadora oficial IFT.
