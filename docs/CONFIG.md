# Guía de configuración

Esta guía explica cómo manejar la configuración local y las API keys de **MeXiCOSINT**.

---

## Archivo de configuración

MeXiCOSINT puede usar un archivo local para guardar API keys y otros valores de configuración.

La ruta recomendada es:

```text
~/.mx_osint_config.json
```

Este archivo debe existir solamente en tu computadora.

No debe subirse a GitHub.

---

## Crear el archivo de configuración

Puedes crear el archivo con:

```bash
nano ~/.mx_osint_config.json
```

Dentro del archivo puedes agregar tus API keys.

Ejemplo:

```json
{
  "abstract_phone_intelligence": "TU_ABSTRACTAPI_KEY",
  "numverify": "TU_NUMVERIFY_KEY",
  "opencage": "TU_OPENCAGE_KEY",
  "geoapify": "TU_GEOAPIFY_KEY",
  "ipqualityscore": "TU_IPQUALITYSCORE_KEY"
}
```

Reemplaza cada valor con tu propia API key.

---

## Proteger el archivo

Para proteger el archivo de configuración local:

```bash
chmod 600 ~/.mx_osint_config.json
```

Esto limita el acceso al archivo únicamente a tu usuario.

---

## APIs opcionales

MeXiCOSINT puede funcionar parcialmente sin API keys.

Sin embargo, algunas funciones tendrán mejores resultados si se configuran servicios externos.

| Servicio    | Función                                                      |
| ----------- | ------------------------------------------------------------ |
| AbstractAPI | Validación y enriquecimiento telefónico como evidencia de apoyo |
| NumVerify   | Validación secundaria como evidencia de apoyo                |
| OpenCage    | Geocodificación primaria opcional de localidad IFT/LADA      |
| Geoapify    | Geocodificación fallback opcional de localidad IFT/LADA      |
| IPQualityScore | Validación, reputación y abuso telefónico como evidencia de apoyo |

---

## Funcionamiento sin API keys

Si no configuras API keys, MeXiCOSINT puede seguir funcionando parcialmente.

Ejemplo:

```text
Sin API keys:
- Validación local
- Parsing básico
- Formato nacional/internacional
- Base IFT/LADA y enlaces OSINT

Con API keys:
- Enriquecimiento adicional
- Validación secundaria
- Geocodificación OpenCage/Geoapify cuando hay localidad concreta
- Fichas públicas de negocio y reputación telefónica
```

---

## Archivos que NO deben subirse

No subas archivos que contengan claves, tokens o datos sensibles.

Ejemplos:

```text
.env
*.env
.mx_osint_config.json
config.json
secrets.json
keys.json
tokens.json
credentials.json
```

Si uno de estos archivos aparece en GitHub por accidente, elimina el archivo y rota las claves afectadas.

Porque sí, una API key subida a GitHub se convierte en comida gratis para bots antes de que termines de pestañear. Qué civilización tan brillante.

---

## Revisar antes de hacer commit

Antes de subir cambios, puedes buscar posibles claves dentro del proyecto:

```bash
grep -Ri "api_key\|apikey\|token\|secret\|password\|credential" .
```

Si aparece una clave real, elimínala antes de hacer commit.

También puedes revisar los archivos modificados con:

```bash
git status
```

Y revisar diferencias con:

```bash
git diff
```

---

## Configuración recomendada en `.gitignore`

El archivo `.gitignore` debe incluir entradas para evitar subir secretos por accidente:

```gitignore
.env
*.env
.mx_osint_config.json
config.json
secrets.json
keys.json
tokens.json
credentials.json
*.key
*.pem
```

---

## Estructura recomendada

La configuración sensible debe vivir fuera del repositorio:

```text
/home/usuario/.mx_osint_config.json
```

o:

```text
~/.mx_osint_config.json
```

El repositorio solo debe contener ejemplos, documentación y código.

---

## Ejemplo seguro para documentación

Si quieres mostrar un ejemplo en la documentación, usa valores falsos:

```json
{
  "abstract_phone_intelligence": "TU_ABSTRACTAPI_KEY",
  "numverify": "TU_NUMVERIFY_KEY",
  "opencage": "TU_OPENCAGE_KEY",
  "geoapify": "TU_GEOAPIFY_KEY",
  "ipqualityscore": "TU_IPQUALITYSCORE_KEY"
}
```

Nunca uses claves reales en ejemplos públicos.

---

## Permisos recomendados

Revisa los permisos actuales:

```bash
ls -la ~/.mx_osint_config.json
```

Aplica permisos seguros:

```bash
chmod 600 ~/.mx_osint_config.json
```

Resultado esperado aproximado:

```text
-rw------- 1 usuario usuario ... /home/usuario/.mx_osint_config.json
```

---

## Si subiste una API key por accidente

1. Elimina la clave del repositorio.
2. Haz commit del cambio.
3. Entra al panel del proveedor de la API.
4. Revoca o elimina la API key expuesta.
5. Crea una API key nueva.
6. Actualiza tu archivo local `~/.mx_osint_config.json`.

No basta con borrar la línea del README o del archivo actual. Git guarda historial. Porque Git es útil, pero también es un archivista con tendencias obsesivas.

---

## Variables de entorno

MeXiCOSINT admite variables de entorno como la fuente de mayor prioridad para resolver API keys. Los nombres propios del proyecto tienen el prefijo `MEXICOSINT_`; también se aceptan los nombres exportados por MicroVault:

```bash
export MEXICOSINT_GEOAPIFY_API_KEY="TU_GEOAPIFY_KEY"
export OPENCAGE_API_KEY="TU_OPENCAGE_KEY"
export NUMVERIFY_API_KEY="TU_NUMVERIFY_KEY"
export IPQUALITYSCORE_API_KEY="TU_IPQS_KEY"  # o IPGS_API_KEY del perfil MicroVault
export ABSTRACT_PHONE_INTELLIGENCE_API_KEY="TU_ABSTRACT_KEY"  # o ABSTRACT_API_KEY
```

Orden de resolución actual:

1. Variables de entorno.
2. MicroVault cifrado.
3. `~/.mx_osint_config.json` (opcional).

Si exportas las keys desde MicroVault, puedes conectarlo automáticamente con:

```bash
eval "$(microvault env)"
mexicosint 5512345678
```

Nunca guardes keys reales en el repositorio ni las incluyas en ejemplos, logs o reportes.

---

## Estados de credenciales y proveedores

MeXiCOSINT no consume créditos para comprobar si una key está válida. Al arrancar solo indica `CONFIGURED_UNVERIFIED`; el estado real se determina durante el escaneo:

| Estado | Significado |
|---|---|
| `MISSING` | No hay una key utilizable para ese proveedor. |
| `NOT_REQUESTED` | El proveedor no recibió una solicitud, normalmente porque no fue necesario. |
| `CONFIGURED_UNVERIFIED` | Hay una key, pero aún no se usó en una solicitud real. |
| `REQUEST_SUCCESS` | El proveedor respondió correctamente. |
| `NO_RESULT` | La respuesta fue válida, pero no contiene un resultado utilizable. |
| `PROVIDER_ERROR` | Error de red, timeout, 5xx o fallo no clasificado. |
| `INVALID_RESPONSE` | La respuesta HTTP fue válida, pero el contenido no coincide con el esquema esperado. |
| `AUTH_FAILED` | Key revocada, inválida o respuesta 401/403. |
| `QUOTA_EXCEEDED` | Cuota o límite de solicitudes agotado. |

La salida incluye la fuente no secreta (`environment`, `microvault`, `json` o `dummy`), el transporte (`live_request`, `cache_hit`, `fixture`, etc.) y errores sanitizados. Nunca imprime la key.

---

## Buenas prácticas

* Mantén tus API keys fuera del repositorio.
* No compartas capturas donde se vean claves.
* No hardcodees API keys dentro del código.
* Usa permisos `600` para archivos sensibles.
* Rota cualquier clave que haya sido expuesta.
* Usa ejemplos falsos en documentación pública.
* Revisa cambios antes de hacer commit.

---

## Estado

Si el archivo existe y tiene permisos correctos, puedes ejecutar:

```bash
bash bin/mexicosint
```

Y MeXiCOSINT debería poder leer la configuración local según las funciones disponibles en la versión actual.
