# Installation guide

## Install from PyPI

```bash
sudo apt install -y pipx
pipx install mexicosint
mexicosint 5512345678
```

To update:

```bash
pipx upgrade mexicosint
```

## Install from the repository

```bash
git clone https://github.com/KiMiGuel/MeXiCOSINT.git
cd MeXiCOSINT
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .
bash bin/mexicosint 5512345678
```

## Credentials

Normal enrichment requires [MicroVault](https://github.com/KiMiGuel/MicroVault)
and its `mexicosint` profile:

```bash
microvault profile mexicosint geoapify opencage_api ipgs numverify_api abstract_api verificaremails
```

MeXiCOSINT does not read generic environment variables or JSON files, and it
does not create a credential configuration file. The bridge strictly uses:

```bash
microvault env --profile mexicosint --json
```

The master password is requested in the interactive terminal. For a run
without remote enrichment:

```bash
mexicosint 5512345678
```

## Security

Do not upload `.env`, JSON files, sensitive reports, or credentials to the
repository. Keys are managed exclusively inside MicroVault.

## Common issues

If `mexicosint` doesn't appear after `pipx install`:

```bash
pipx ensurepath
```

Close and reopen the terminal. For an install from the repository, activate
the virtual environment before running the launcher.

## Status

```bash
mexicosint --version
mexicosint 5512345678
```
