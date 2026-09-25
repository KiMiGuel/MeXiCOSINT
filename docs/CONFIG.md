# Configuración y credenciales

MeXiCOSINT usa **MicroVault como único backend de credenciales** para el enriquecimiento normal de proveedores.

## Contrato de credenciales

- Los escaneos normales requieren el perfil de MicroVault llamado `mexicosint`.
- MeXiCOSINT consulta ese perfil mediante el bridge local y el comando
  `microvault env --profile mexicosint --json`.
- No hay fallback a un vault completo, a servicios individuales, a variables
  de entorno genéricas ni a archivos JSON.
- MeXiCOSINT no crea, lee ni escribe archivos de configuración de credenciales.
- La contraseña maestra se solicita mediante MicroVault en una terminal interactiva.
- El modo dummy es la única excepción: usa fixtures en memoria y no consume
  credenciales.

## Configurar el perfil

En MicroVault, guarda las credenciales que quieras usar y crea el perfil:

```bash
microvault profile mexicosint geoapify opencage_api ipgs numverify_api abstract_api verificaremails
```

Los nombres de servicio esperados por MeXiCOSINT son:

| Servicio MeXiCOSINT | Nombre en MicroVault |
|---|---|
| AbstractAPI | `abstract_api` |
| NumVerify | `numverify_api` |
| OpenCage | `opencage_api` |
| Geoapify | `geoapify` |
| IPQualityScore | `ipgs` |
| Verificar Emails | `verificaremails` |


Después ejecuta normalmente:

```bash
mexicosint 5512345678
```

La configuración de estas credenciales se hace exclusivamente en MicroVault;
MeXiCOSINT no ofrece comandos para guardar o listar keys.

## Opciones de ejecución

`--microvault` forces the required profile connection. There is no alternate
credential path; normal scans use the MicroVault profile, while dummy mode
uses in-memory fixtures.

## Seguridad

Nunca guardes keys en el repositorio ni las incluyas en logs, reportes o
ejemplos. Si una credencial se expone, revócala en el proveedor y reemplázala
en MicroVault.

Para verificar secretos antes de hacer commit:

```bash
grep -RiE "api[_-]?key|token|secret|password|credential" .
```

## Estados de proveedores

`CONFIGURED_UNVERIFIED` significa que el perfil entregó una key, pero todavía
no se validó contra el proveedor. `MISSING` significa que el perfil no entregó
esa key. La fuente reportada es `microvault` o `dummy`; no se reportan
variables de entorno ni JSON.
