# Guía de uso

Esta guía explica el uso básico de **MeXiCOSINT**.

---

## Ejecutar la herramienta

Desde la carpeta del repositorio:

```bash
cd MeXiCOSINT

Activa el entorno virtual:

source venv/bin/activate

Ejecuta el script:

python3 mexicosint_v2.2.5.py
Flujo básico

La herramienta solicitará un número telefónico mexicano para analizar.

Formato recomendado:

+52XXXXXXXXXX

También puedes probar con formato nacional:

XXXXXXXXXX
Resultados

MeXiCOSINT puede mostrar información como:

Validez del número
Formato nacional e internacional
Región o referencia LADA
Operador o fuente asociada, si está disponible
Resultados de APIs configuradas
Consenso aproximado entre fuentes
Reporte exportable, si la opción está disponible
Reportes

Si la herramienta genera reportes, revisa la carpeta del proyecto después de ejecutarla.

Ejemplos de posibles archivos generados:

reporte.json
reporte.html
reporte_mapa.html

Los nombres exactos pueden variar según la versión.

API keys

Algunas funciones dependen de servicios externos.

Si no configuras API keys, la herramienta puede seguir funcionando parcialmente, pero los resultados serán más limitados.

No subas tus API keys a GitHub.

Modo de prueba

Si la herramienta incluye un modo dummy o de prueba, úsalo solamente para desarrollo local.

Ejemplo:

python3 mexicosint_v2.2.5.py --dummy-test

Este modo puede cambiar o desaparecer en futuras versiones.

Buenas prácticas
Verifica resultados con más de una fuente.
No tomes resultados OSINT como prueba absoluta.
No uses la herramienta para acoso, doxxing o actividad no autorizada.
Mantén tus API keys fuera del repositorio.
Salir del entorno virtual

Cuando termines:

deactivate
