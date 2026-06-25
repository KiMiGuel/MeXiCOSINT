# Guía de uso

Esta guía explica cómo ejecutar y usar **MeXiCOSINT** después de instalarlo.

---

## Antes de empezar

Asegúrate de estar dentro de la carpeta del proyecto:

```bash
cd MeXiCOSINT
```

Activa el entorno virtual:

```bash
source venv/bin/activate
```

Si el entorno virtual está activo, tu terminal debería mostrar algo parecido a:

```text
(venv) usuario@equipo:~/MeXiCOSINT$
```

---

## Ejecutar MeXiCOSINT

La forma recomendada es usar el launcher incluido:

```bash
bash bin/mexicosint
```

También puedes ejecutar directamente el archivo principal:

```bash
python3 mexicosint_v2.2.5.py
```

---

## Formato recomendado del número

MeXiCOSINT está enfocado en números telefónicos mexicanos.

Formato recomendado:

```text
+52XXXXXXXXXX
```

También puede aceptar formato nacional de 10 dígitos:

```text
XXXXXXXXXX
```

Ejemplo de formato internacional:

```text
+525512345678
```

Ejemplo de formato nacional:

```text
5512345678
```

---

## Flujo básico de uso

1. Ejecuta la herramienta:

```bash
bash bin/mexicosint
```

2. Ingresa el número telefónico cuando la herramienta lo solicite.

3. Revisa los resultados mostrados en terminal.

4. Si la herramienta genera reportes, revisa los archivos creados dentro del proyecto.

---

## Resultados posibles

Dependiendo de la versión, configuración y API keys disponibles, MeXiCOSINT puede mostrar información como:

* Validación del número
* Formato nacional
* Formato internacional
* Código de país
* Región o referencia LADA
* Operador o fuente asociada, si está disponible
* Información obtenida desde módulos locales
* Información obtenida desde APIs externas configuradas
* Consenso aproximado entre fuentes
* Reportes exportables

---

## APIs y resultados limitados

MeXiCOSINT puede funcionar parcialmente sin API keys.

Sin embargo, algunas funciones pueden estar limitadas si no configuraste servicios externos.

Ejemplo:

```text
Sin API key: validación local y parsing básico
Con API key: enriquecimiento adicional según el servicio configurado
```

Para configurar API keys, revisa:

```text
docs/CONFIG.md
```

---

## Reportes y archivos generados

Si la herramienta genera reportes, pueden aparecer archivos como:

```text
reporte.json
```

```text
reporte.html
```

```text
reporte_mapa.html
```

Los nombres exactos pueden cambiar según la versión.

También puede haber carpetas como:

```text
reports/
```

```text
output/
```

```text
results/
```

Si no aparece ningún reporte, revisa la salida en terminal para confirmar si la función está disponible en tu versión.

---

## Modo de prueba o desarrollo

Si la versión incluye un modo de prueba, puede ejecutarse con una bandera especial.

Ejemplo:

```bash
python3 mexicosint_v2.2.5.py --dummy-test
```

Este modo está pensado para desarrollo local.

No debe considerarse una función principal para usuarios finales.

---

## Actualizar antes de usar

Para actualizar el repositorio:

```bash
git pull
```

Después, si cambiaron las dependencias:

```bash
pip install -r requirements.txt
```

---

## Salir del entorno virtual

Cuando termines:

```bash
deactivate
```

---

## Buenas prácticas

* Verifica resultados con más de una fuente.
* No trates resultados OSINT como evidencia absoluta.
* No subas API keys a GitHub.
* No publiques reportes con información sensible.
* Usa la herramienta únicamente en investigaciones autorizadas, autoauditoría o fines educativos.

---

## Solución rápida de problemas

### El comando `bash bin/mexicosint` no funciona

Confirma que estás dentro de la carpeta del proyecto:

```bash
pwd
```

Confirma que existe el launcher:

```bash
ls -la bin
```

Ejecuta otra vez:

```bash
bash bin/mexicosint
```

---

### Error de dependencias

Vuelve a instalar los requisitos:

```bash
pip install -r requirements.txt
```

---

### Error con el entorno virtual

Recrea el entorno virtual:

```bash
rm -rf venv
```

```bash
python3 -m venv venv
```

```bash
source venv/bin/activate
```

```bash
pip install -r requirements.txt
```

---

### API key no detectada

Revisa que el archivo de configuración exista:

```bash
ls -la ~/.mx_osint_config.json
```

Revisa permisos:

```bash
chmod 600 ~/.mx_osint_config.json
```

Revisa la guía de configuración:

```text
docs/CONFIG.md
```

---

## Estado

Si todo está correcto, deberías poder ejecutar:

```bash
bash bin/mexicosint
```

Y ver el inicio de MeXiCOSINT en terminal.
