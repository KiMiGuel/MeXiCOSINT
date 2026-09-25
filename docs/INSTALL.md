# Guía de instalación

## Instalación desde PyPI

```bash
sudo apt install -y pipx
pipx install mexicosint
mexicosint 5512345678
```

Para actualizar:

```bash
pipx upgrade mexicosint
```

## Instalación desde el repositorio

```bash
git clone https://github.com/KiMiGuel/MeXiCOSINT.git
cd MeXiCOSINT
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .
bash bin/mexicosint 5512345678
```

## Credenciales

El enriquecimiento normal requiere [MicroVault](https://github.com/KiMiGuel/MicroVault)
y su perfil `mexicosint`:

```bash
microvault profile mexicosint geoapify opencage_api ipgs numverify_api abstract_api verificaremails
```

MeXiCOSINT no lee variables de entorno genéricas ni archivos JSON, y no crea un
archivo de configuración de credenciales. El bridge usa estrictamente:

```bash
microvault env --profile mexicosint --json
```

La contraseña maestra se solicita en la terminal interactiva. Para una ejecución
sin enriquecimiento remoto:

```bash
mexicosint 5512345678
```

## Seguridad

No subas `.env`, archivos JSON, reportes sensibles ni credenciales al repositorio.
Las keys se administran únicamente dentro de MicroVault.

## Problemas comunes

Si `mexicosint` no aparece tras `pipx install`:

```bash
pipx ensurepath
```

Cierra y vuelve a abrir la terminal. Para una instalación desde el repositorio,
activa el entorno virtual antes de ejecutar el launcher.

## Estado

```bash
mexicosint --version
mexicosint 5512345678
```
