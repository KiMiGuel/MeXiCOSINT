# Guía de configuración

Esta guía explica cómo manejar la configuración local y las API keys de **MeXiCOSINT**.

---

## Archivo de configuración

MeXiCOSINT puede usar un archivo local para guardar API keys y otros valores de configuración.

La ruta recomendada es:

```text
~/.mx_osint_config.json
```

Este archivo debe existir solamente en tu computadora y no debe subirse a GitHub.

---

## Crear el archivo de configuración

La primera ejecución puede crear un archivo base. También puedes crearlo manualmente:

```bash
nano ~/.mx_osint_config.json
```

Ejemplo:

```json
{
  "abstract_phone_intelligence": "TU_ABSTRACTAPI_KEY",
  "numverify": "TU_NUMVERIFY_KEY",
  "shodan": "TU_SHODAN_KEY",
  "ipinfo": "TU_IPINFO_KEY",
  "ip2location": "TU_IP2LOCATION_KEY",
  "opencage": "TU_OPENCAGE_KEY"
}
```

Reemplaza cada valor con tu propia API key.

---

## Proteger el archivo

```bash
chmod 600 ~/.mx_osint_config.json
```

Esto limita el acceso del archivo únicamente a tu usuario.

---

## APIs opcionales

MeXiCOSINT puede funcionar parcialmente sin API keys. Algunas funciones tendrán mejores resultados si configuras servicios externos.

| Servicio    | Función                                                      |
| ----------- | ------------------------------------------------------------ |
| AbstractAPI | Validación y enriquecimiento de números telefónicos          |
| NumVerify   | Validación secundaria de números telefónicos                 |
| Shodan      | Enriquecimiento opcional relacionado con servicios expuestos |
| IPInfo      | Enriquecimiento de metadatos IP                              |
| IP2Location | Enriquecimiento de metadatos IP                              |
| OpenCage    | Geocodificación y soporte para mapas                         |

---

## Archivos que NO deben subirse

No subas archivos que contengan claves, tokens o datos sensibles.

```text
.env
*.env
.mx_osint_config.json
config.json
secrets.json
keys.json
tokens.json
credentials.json
*.local.json
*.config.json
```

Si una clave llega a GitHub por accidente, elimina el archivo del repositorio y rota las claves afectadas.

---

## Revisar antes de hacer commit

```bash
grep -Ri "api_key\|apikey\|token\|secret\|password\|credential" .
git status
git diff
```

---

## Configuración recomendada en `.gitignore`

```gitignore
.env
*.env
.mx_osint_config.json
config.json
secrets.json
keys.json
tokens.json
credentials.json
*.local.json
*.config.json
*.key
*.pem
```

---

## Ejecución con configuración local

Después de instalar el paquete:

```bash
mexicosint --number 5512345678
```

Modo IP directo:

```bash
mexicosint --ip 8.8.8.8
```

---

## Buenas prácticas

* Mantén tus API keys fuera del repositorio.
* No compartas capturas donde se vean claves.
* No hardcodees API keys dentro del código.
* Usa permisos `600` para archivos sensibles.
* Rota cualquier clave que haya sido expuesta.
* Usa ejemplos falsos en documentación pública.
* Revisa cambios antes de hacer commit.
