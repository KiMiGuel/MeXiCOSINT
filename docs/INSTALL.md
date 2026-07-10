# Guía de instalación

Esta guía explica cómo instalar **MeXiCOSINT** en Kali Linux, Debian, Ubuntu y sistemas similares.

---

## Requisitos

Antes de instalar MeXiCOSINT, asegúrate de tener instalados los paquetes básicos necesarios:

- Python 3
- pip
- venv
- git

Instala los requisitos base con:

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git
```

---

## Clonar el repositorio

```bash
git clone https://github.com/KiMiGuel/MeXiCOSINT.git
cd MeXiCOSINT
```

---

## Crear entorno virtual

Se recomienda usar un entorno virtual para evitar conflictos con paquetes del sistema.

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## Instalar el paquete

Instala MeXiCOSINT en modo editable desde la raíz del repositorio:

```bash
pip install -e .
```

Para desarrollo, también puedes instalar desde `requirements.txt`:

```bash
pip install -r requirements.txt
```

---

## Ejecutar MeXiCOSINT

La forma recomendada es usar el comando instalado:

```bash
mexicosint --number 5512345678
```

También puedes ejecutar el módulo del paquete sin instalar el comando global:

```bash
PYTHONPATH=src python3 -m mexicosint --number 5512345678
```

---

## Configuración de API keys

MeXiCOSINT puede usar API keys externas para mejorar los resultados.

El archivo recomendado para configuración local es:

```text
~/.mx_osint_config.json
```

Este archivo debe quedarse en tu computadora y no debe subirse a GitHub.

---

## Proteger archivo de configuración

```bash
chmod 600 ~/.mx_osint_config.json
```

---

## Actualizar MeXiCOSINT

```bash
git pull
pip install -e .
```

Si las dependencias cambiaron, vuelve a ejecutar:

```bash
pip install -r requirements.txt
```

---

## Salir del entorno virtual

```bash
deactivate
```

---

## Instalación rápida

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git
git clone https://github.com/KiMiGuel/MeXiCOSINT.git
cd MeXiCOSINT
python3 -m venv venv
source venv/bin/activate
pip install -e .
mexicosint --number 5512345678
```

---

## Notas importantes

- No subas API keys a GitHub.
- Usa un entorno virtual para evitar romper paquetes del sistema.
- Si estás en Kali Linux moderno, evita instalar paquetes Python globalmente con `sudo pip`.
- Los resultados OSINT deben verificarse con más de una fuente.
- La herramienta está pensada para investigación autorizada, autoauditoría y fines educativos.

---

## Problemas comunes

### `python3: command not found`

```bash
sudo apt install -y python3
```

### `pip: command not found`

```bash
sudo apt install -y python3-pip
```

### Error creando el entorno virtual

```bash
sudo apt install -y python3-venv
```

### El comando `mexicosint` no existe

Confirma que el entorno virtual está activo y reinstala el paquete:

```bash
source venv/bin/activate
pip install -e .
```

---

## Estado

Si la instalación terminó correctamente, deberías poder ejecutar:

```bash
mexicosint --number 5512345678
```
