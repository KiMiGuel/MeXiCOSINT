# Guía de uso

Esta guía explica cómo ejecutar y usar **MeXiCOSINT** después de instalarlo.

---

## Antes de empezar

Activa el entorno virtual donde instalaste el paquete:

```bash
source venv/bin/activate
```

---

## Ejecutar MeXiCOSINT

La forma recomendada es usar el comando instalado:

```bash
mexicosint --number 5512345678
```

También puedes usar el número como argumento posicional por compatibilidad:

```bash
mexicosint 5512345678
```

Para ejecutar sin instalar el comando global:

```bash
PYTHONPATH=src python3 -m mexicosint --number 5512345678
```

---

## Formato recomendado del número

MeXiCOSINT está enfocado en números telefónicos mexicanos.

Formato internacional:

```text
+52XXXXXXXXXX
```

Formato nacional de 10 dígitos:

```text
XXXXXXXXXX
```

Ejemplos:

```bash
mexicosint --number +525512345678
mexicosint --number 5512345678
```

---

## Opciones principales

```bash
mexicosint --number 5512345678
mexicosint --ip 8.8.8.8
mexicosint --dummy-test --number 5512345678
mexicosint -b --number 5512345678
mexicosint --version
```

`-b`, `--compact-banner` y `--small-banner` fuerzan el banner compacto.

---

## Resultados posibles

Dependiendo de la configuración y API keys disponibles, MeXiCOSINT puede mostrar información como:

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

MeXiCOSINT puede funcionar parcialmente sin API keys. Algunas funciones estarán limitadas si no configuraste servicios externos.

```text
Sin API key: validación local y parsing básico
Con API key: enriquecimiento adicional según el servicio configurado
```

Para configurar API keys, revisa `docs/CONFIG.md`.

---

## Reportes y archivos generados

Los reportes generados se escriben dentro de carpetas ignoradas por Git, como:

```text
output/
reports/
results/
```

No publiques reportes con información sensible.

---

## Actualizar antes de usar

```bash
git pull
pip install -e .
```

Si cambiaron las dependencias:

```bash
pip install -r requirements.txt
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

### El comando `mexicosint` no funciona

Confirma que el entorno virtual está activo y que el paquete fue instalado:

```bash
source venv/bin/activate
pip install -e .
```

### Error de dependencias

```bash
pip install -r requirements.txt
```

### API key no detectada

```bash
ls -la ~/.mx_osint_config.json
chmod 600 ~/.mx_osint_config.json
```

Revisa `docs/CONFIG.md`.
