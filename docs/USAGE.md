# Guía de uso

## Escanear

```bash
mexicosint 5512345678
mexicosint +525512345678
mexicosint "52-663-464-7308"
```

Los números送上 se normalizan y validan; los proveedores opcionales se
consultan solo cuando el perfil MicroVault `mexicosint` aporta su credencial.

## Opciones

```text
mexicosint [-h] [--batch FILE] [--mexico-only] [--microvault] [--version] [number]
```

| Opción | Descripción |
|---|---|
| `number` | Número telefónico mexicano a escanear |
| `--batch FILE` | Procesa un archivo con un número por línea |
| `--mexico-only` | Omite proveedores externos de teléfono; conserva IFT/PNN y geocodificación aproximada |
| `--microvault` | Fuerza la conexión al perfil `mexicosint` |
| `--version` | Muestra la versión instalada |
| `-h`, `--help` | Muestra la ayuda |

No existen opciones de MeXiCOSINT para crear, guardar o listar keys: la
configuración se hace en MicroVault.

## Configuración de credenciales

```bash
microvault profile mexicosint geoapify opencage_api ipgs numverify_api abstract_api
```

El bridge consulta una sola vez:

```bash
microvault env --profile mexicosint --json
```

No hay fallback a `microvault env`, `microvault env <servicio>`, variables de
entorno genéricas ni archivos JSON. Si falta el perfil, MicroVault o la
interacción de contraseña, el enriquecimiento remoto no se realiza; usa
`--microvault` para hacer fallar el escaneo ante un problema de conexión.

## Modo dummy

El flag interno `--dummy-test` usa fixtures en memoria y no requiere
MicroVault, variables de entorno ni archivos de credenciales.

## Funciones y proveedores

- Validación, formato y análisis local.
- Base oficial IFT/PNN y LADA sin red.
- Enlaces OSINT.
- Enriquecimiento opcional de AbstractAPI, NumVerify, IPQualityScore.
- OpenCage y Geoapify para localidad concreta.
- Nominatim como geocodificador final sin credenciales.

## Seguridad

No subas credenciales, `.env`, archivos JSON, reportes sensibles ni capturas
que las contengan. MeXiCOSINT no crea ni modifica archivos JSON de
configuración. Si una credencial fue expuesta, revócala en el proveedor y
reemplázala en MicroVault.

## Solución de problemas

### API enrichment not available

Comprueba que MicroVault esté instalado, que el perfil exista y que el comando
se ejecute desde una terminal interactiva:

```bash
microvault profile
mexicosint --microvault 5512345678
```

### IFT no aparece

La base viene incluida. Para regenerarla:

```bash
python3 tools/update_ift_blocks.py --offline
```
