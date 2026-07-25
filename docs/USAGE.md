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
```

---

## Todas las opciones

```text
mexicosint [-h] [--ip ADDRESS] [--dummy-test] [-b]
           [--set-key SERVICIO KEY] [--list-keys] [--config-path]
           [--version] [number]
```

| Opción | Descripción |
|---|---|
| `number` | Número telefónico mexicano a escanear |
| `--ip ADDRESS` | Geolocaliza una IP pública (combinable con número) |
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

Geolocalizar una IP pública:

```bash
mexicosint --ip 8.8.8.8
```

Escaneo combinado número + IP (el orden no importa):

```bash
mexicosint 5512345678 --ip 8.8.8.8
mexicosint --ip 8.8.8.8 5512345678
```

Prueba sin consumir créditos de API:

```bash
mexicosint --dummy-test 5512345678
```

Banner compacto:

```bash
mexicosint -b 5512345678
```

> Nota: las IPs privadas (192.168.x.x, 10.x.x.x, etc.) se detectan automáticamente y no consumen llamadas a APIs.

---

## Gestión de API keys

Ya no necesitas editar el archivo de configuración a mano.

Guardar una key:

```bash
mexicosint --set-key opencage TU_KEY
mexicosint --set-key shodan TU_KEY
mexicosint --set-key abstract TU_KEY
```

Servicios válidos: `abstract` (alias de `abstract_phone_intelligence`), `numverify`, `shodan`, `ip2location`, `ipinfo`, `opencage`.

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

Desde la versión 2.4.0, MeXiCOSINT incluye la **base oficial del Plan Nacional de Numeración (IFT)** integrada — más de 177,000 bloques de numeración asignada en México, consultada **offline** (sin internet, sin API keys).

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
* Operadora y ubicación reportadas por APIs (Abstract, NumVerify)
* Consenso de ubicación entre fuentes
* Enlaces de investigación OSINT
* Resultados Shodan (si la key está configurada)
* Geolocalización aproximada de la localidad + mapa HTML
* Reporte JSON exportado en `output/reports/`

> Los enlaces OSINT completos también quedan guardados en el reporte JSON.

---

## Sin API keys

MeXiCOSINT funciona parcialmente sin keys:

```text
Sin API keys: validación, parsing local, base IFT completa, LADA, enlaces OSINT
Con API keys: enriquecimiento adicional, consenso entre fuentes, mapas, Shodan
```

La base IFT funciona siempre, con o sin keys.

---

## Modo de prueba

```bash
mexicosint --dummy-test 5512345678
```

Usa datos de ejemplo y no realiza llamadas reales a APIs. Pensado para desarrollo y pruebas.

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

debería mostrar el banner, la información del suscriptor y la operadora oficial IFT.
