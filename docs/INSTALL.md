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
```

```bash
sudo apt install -y python3 python3-pip python3-venv git
```

---

## Clonar el repositorio

Clona el repositorio desde GitHub:

```bash
git clone https://github.com/KiMiGuel/MeXiCOSINT.git
```

Entra a la carpeta del proyecto:

```bash
cd MeXiCOSINT
```

---

## Crear entorno virtual

Se recomienda usar un entorno virtual para evitar conflictos con paquetes del sistema.

Crea el entorno virtual:

```bash
python3 -m venv venv
```

Activa el entorno virtual:

```bash
source venv/bin/activate
```

Cuando el entorno virtual esté activo, tu terminal debería mostrar algo parecido a:

```text
(venv) usuario@equipo:~/MeXiCOSINT$
```

---

## Instalar dependencias

Instala las dependencias del proyecto:

```bash
pip install -r requirements.txt
```

Si todo sale correctamente, MeXiCOSINT estará listo para ejecutarse.

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

Para actualizar el repositorio:

```bash
git pull
```

Si las dependencias cambiaron, vuelve a ejecutar:

```bash
pip install -r requirements.txt
```

---

## Salir del entorno virtual

Cuando termines de usar la herramienta:

```bash
deactivate
```

---

## Instalación rápida

Resumen completo:

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
- Usa un entorno virtual para evitar romper paquetes del sistema.
- Si estás en Kali Linux moderno, evita instalar paquetes Python globalmente con `sudo pip`.
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
bash bin/mexicosint
```

Y ver el inicio de MeXiCOSINT en la terminal.
