# Guía de instalación

Esta guía explica cómo instalar **MeXiCOSINT** en Kali Linux, Debian, Ubuntu y sistemas similares.

---

## Instalación desde PyPI (recomendada)

MeXiCOSINT está publicado en PyPI, así que no necesitas clonar el repositorio para usarlo.

### Opción A: pipx (recomendada para Kali)

`pipx` instala la herramienta en un entorno aislado y deja el comando `mexicosint` disponible globalmente, sin tocar el Python del sistema.

En Kali Linux moderno esto es importante: `pip install` global está bloqueado por PEP 668 (`externally-managed-environment`), y `pipx` es la solución oficial.

Instala pipx:

```bash
sudo apt update
sudo apt install -y pipx
```

Instala MeXiCOSINT:

```bash
pipx install mexicosint
```

Ejecuta:

```bash
mexicosint
```

Actualizar a una nueva versión:

```bash
pipx upgrade mexicosint
```

Desinstalar:

```bash
pipx uninstall mexicosint
```

### Opción B: pip directo

En sistemas sin PEP 668:

```bash
pip install mexicosint
```

En Kali, si insistes en pip global:

```bash
pip install mexicosint --break-system-packages
```

> Se recomienda `pipx` en su lugar. `--break-system-packages` puede romper paquetes Python del sistema.

---

## Instalación desde el repositorio (para desarrollo)

Usa este método si quieres modificar el código o colaborar.

### Requisitos

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git
```

### Clonar el repositorio

```bash
git clone https://github.com/KiMiGuel/MeXiCOSINT.git
cd MeXiCOSINT
```

### Crear entorno virtual

```bash
python3 -m venv venv
source venv/bin/activate
```

Cuando el entorno virtual esté activo, tu terminal debería mostrar algo parecido a:

```text
(venv) usuario@equipo:~/MeXiCOSINT$
```

### Instalar dependencias

```bash
pip install -r requirements.txt
```

Opcionalmente, instala el paquete en modo editable:

```bash
pip install -e .
```

### Ejecutar desde el repositorio

Con el launcher incluido:

```bash
bash bin/mexicosint
```

O directamente como módulo:

```bash
PYTHONPATH=src python3 -m mexicosint
```

### Salir del entorno virtual

```bash
deactivate
```

---

## Configuración de API keys

MeXiCOSINT puede usar API keys externas para mejorar los resultados.

El archivo recomendado para configuración local es:

```text
~/.mx_osint_config.json
```

Este archivo debe quedarse en tu computadora.

No debe subirse a GitHub.

---

## Proteger archivo de configuración

Para proteger el archivo de configuración local:

```bash
chmod 600 ~/.mx_osint_config.json
```

---

## Actualizar MeXiCOSINT

Si instalaste con pipx:

```bash
pipx upgrade mexicosint
```

Si instalaste con pip:

```bash
pip install --upgrade mexicosint
```

Si clonaste el repositorio:

```bash
git pull
pip install -r requirements.txt
```

---

## Instalación rápida

Resumen completo (método pipx):

```bash
sudo apt update
sudo apt install -y pipx
pipx install mexicosint
mexicosint
```

Resumen completo (método repositorio):

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git
git clone https://github.com/KiMiGuel/MeXiCOSINT.git
cd MeXiCOSINT
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
bash bin/mexicosint
```

---

## Notas importantes

- No subas API keys a GitHub.
- Usa pipx o un entorno virtual para evitar romper paquetes del sistema.
- En Kali Linux moderno, evita instalar paquetes Python globalmente con `sudo pip`.
- Los resultados OSINT deben verificarse con más de una fuente.
- La herramienta está pensada para investigación autorizada, autoauditoría y fines educativos.

---

## Problemas comunes

### `python3: command not found`

Instala Python:

```bash
sudo apt install -y python3
```

### `pip: command not found`

Instala pip:

```bash
sudo apt install -y python3-pip
```

### `pipx: command not found`

Instala pipx:

```bash
sudo apt install -y pipx
```

Si el comando `mexicosint` no aparece después de instalar con pipx, asegura el PATH:

```bash
pipx ensurepath
```

Cierra y vuelve a abrir la terminal después.

### `error: externally-managed-environment`

Estás intentando usar `pip install` global en un sistema con PEP 668 (Kali/Debian/Ubuntu modernos). Usa `pipx install mexicosint` en su lugar.

### Error creando el entorno virtual

Instala venv:

```bash
sudo apt install -y python3-venv
```

### Error de permisos

Asegúrate de estar dentro de la carpeta del proyecto y de tener permisos sobre los archivos.

```bash
pwd
```

```bash
ls -la
```

---

## Estado

Si la instalación terminó correctamente, deberías poder ejecutar:

```bash
mexicosint
```

Y ver el inicio de MeXiCOSINT en la terminal.
