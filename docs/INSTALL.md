# Guía de instalación

Esta guía explica cómo instalar **MeXiCOSINT** en Kali Linux, Debian, Ubuntu y sistemas similares.

---

## Requisitos

Antes de instalar, asegúrate de tener:

- Python 3
- pip
- git
- venv

Instala los requisitos base:

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git
Instalación

Clona el repositorio:

git clone https://github.com/metalpunx666/MeXiCOSINT.git

Entra al directorio:

cd MeXiCOSINT

Crea un entorno virtual:

python3 -m venv venv

Activa el entorno virtual:

source venv/bin/activate

Instala las dependencias:

pip install -r requirements.txt
Uso básico

Ejecuta la herramienta:

python3 mexicosint_v2.2.5.py
Configuración de API keys

La herramienta puede crear o usar un archivo de configuración local para guardar tus claves de API.

El archivo de configuración local no debe subirse a GitHub.

Ejemplo recomendado:

~/.mx_osint_config.json

Protege el archivo:

chmod 600 ~/.mx_osint_config.json
Actualizar MeXiCOSINT

Para actualizar el repositorio:

git pull

Después, actualiza dependencias si cambian:

pip install -r requirements.txt
Notas
No subas API keys al repositorio.
Usa la herramienta únicamente en investigaciones autorizadas.
Los resultados deben tratarse como indicadores OSINT, no como evidencia definitiva.
