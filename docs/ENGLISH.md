# MeXiCOSINT English Documentation

**MeXiCOSINT** is a Python-based OSINT tool focused on Mexican phone number analysis, validation, enrichment, and reporting.

This document provides the full English documentation for installation, usage, configuration, security notes, troubleshooting, and project status.

---

## Overview

MeXiCOSINT is designed for authorized OSINT research, self-auditing, and educational workflows involving Mexican phone numbers.

The tool can validate numbers, parse Mexican phone formats, use optional external API sources, process available metadata, and generate investigation-style output depending on the active version and configuration.

> This project is currently in beta. Results should be treated as OSINT indicators, not absolute proof.

---

## Features

* Mexican phone number validation
* National and international number formatting
* Local parsing for Mexican numbers
* Optional API enrichment
* IFT/SNS-related processing
* QuienHabla.mx module support
* Launcher script for cleaner execution
* Local API key configuration
* Report or output support depending on version
* Development/testing support depending on version
* **Official IFT/PNN block database (v2.5.0)** — 177k+ assigned numbering blocks, offline
* Carrier, modality (fixed/mobile), and assignment date straight from the regulator
* Non-geographic series 200/300/500/800/900 identification (toll-free, premium-rate alerts)
* CLI API key management (`--set-key`, `--list-keys`, `--config-path`)
* Combined number + IP scan in a single run, order-independent
* Private/reserved IP guard (no wasted API calls on RFC 1918 addresses)

---

## Repository Structure

```text
MeXiCOSINT/
├── bin/
│   └── mexicosint
├── docs/
│   ├── INSTALL.md
│   ├── USAGE.md
│   ├── CONFIG.md
│   └── ENGLISH.md
├── src/
│   └── mexicosint/
│       ├── cli.py
│       ├── main.py
│       ├── data/
│       ├── modules/
│       ├── services/
│       └── utils/
├── tools/
│   └── update_ift_blocks.py
├── pyproject.toml
├── requirements.txt
├── .gitignore
├── LICENSE
└── README.md
```

---

## Requirements

Before installing MeXiCOSINT, make sure your system has:

* Python 3
* pip (or pipx)
* git (only if installing from the repository)

Install the basic requirements on Kali Linux, Debian, Ubuntu, or similar systems:

```bash
sudo apt update
```

```bash
sudo apt install -y python3 python3-pip python3-venv git
```

---

## Installation from PyPI (recommended)

MeXiCOSINT is published on PyPI, so you do not need to clone the repository just to use it.

### Option A: pipx (recommended for Kali)

`pipx` installs the tool in an isolated environment and exposes the `mexicosint` command globally, without touching the system Python.

This matters on modern Kali Linux: global `pip install` is blocked by PEP 668 (`externally-managed-environment`), and `pipx` is the official workaround.

Install pipx:

```bash
sudo apt update
sudo apt install -y pipx
```

Install MeXiCOSINT:

```bash
pipx install mexicosint
```

Run it:

```bash
mexicosint
```

Upgrade to a new version:

```bash
pipx upgrade mexicosint
```

Uninstall:

```bash
pipx uninstall mexicosint
```

### Option B: plain pip

On systems without PEP 668:

```bash
pip install mexicosint
```

On Kali, if you insist on global pip:

```bash
pip install mexicosint --break-system-packages
```

> pipx is recommended instead. `--break-system-packages` can break system Python packages.

---

## Installation from the Repository (for development)

Use this method if you want to modify the code or contribute.

Clone the repository:

```bash
git clone https://github.com/KiMiGuel/MeXiCOSINT.git
```

Enter the project folder:

```bash
cd MeXiCOSINT
```

Create a virtual environment:

```bash
python3 -m venv venv
```

Activate the virtual environment:

```bash
source venv/bin/activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

Optionally, install the package in editable mode:

```bash
pip install -e .
```

Run from the repository using the included launcher:

```bash
bash bin/mexicosint
```

Or run the package module directly:

```bash
PYTHONPATH=src python3 -m mexicosint
```

When you are done, exit the virtual environment:

```bash
deactivate
```

---

## Quick Installation

Full setup summary (pipx method):

```bash
sudo apt update
sudo apt install -y pipx
pipx install mexicosint
mexicosint
```

Full setup summary (repository method):

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

## Usage

If you installed from PyPI (pipx or pip), run the command directly:

```bash
mexicosint 5512345678
```

Force the compact ASCII banner:

```bash
mexicosint -b 5512345678
```

Combined number + IP scan (order-independent):

```bash
mexicosint 5512345678
mexicosint "+52 663 464 7308"
```

API key management:

```bash
mexicosint --set-key geoapify YOUR_KEY
mexicosint --list-keys
mexicosint --config-path
```

> Private IPs (192.168.x.x, 10.x.x.x, ...) are detected automatically and skip API calls.

If you cloned the repository, make sure you are inside the project folder and the virtual environment is active, then use the launcher:

```bash
bash bin/mexicosint 5512345678
```

Or the module form:

```bash
PYTHONPATH=src python3 -m mexicosint 5512345678
```

---

## Recommended Phone Number Format

MeXiCOSINT is focused on Mexican phone numbers.

Recommended international format:

```text
+52XXXXXXXXXX
```

National 10-digit format may also be accepted:

```text
XXXXXXXXXX
```

Example international format:

```text
+525512345678
```

Example national format:

```text
5512345678
```

---

## Basic Workflow

1. Run the tool:

```bash
mexicosint
```

2. Enter the Mexican phone number when prompted.

3. Review the terminal output.

4. If the tool generates reports, check the files created inside the project folder.

---

## Possible Results

Depending on the version, configuration, and available API keys, MeXiCOSINT may display information such as:

* Number validation
* National format
* International format
* Country code
* Region or LADA reference
* Carrier or source data, if available
* Local module results
* External API results, if configured
* Approximate consensus between sources
* Exportable reports

---

## Official IFT/PNN Database (v2.5.0)

MeXiCOSINT ships with the official Plan Nacional de Numeracion block registry from the IFT (Mexico's telecom regulator): 177,000+ assigned numbering blocks, queried **offline** — no internet, no API keys.

Every scan can show:

| Field | Description |
|---|---|
| Operadora (IFT oficial) | Concessionaire that owns the block, from the regulator (e.g. Telcel, Telmex, AT&T) |
| Modalidad (IFT) | Fixed line, Mobile (CPP/MPP), or Non-geographic |
| Asignado (IFT) | Date the block was assigned to the concessionaire |
| Tipo de servicio (IFT) | Non-geographic series only: 800 (toll-free), 900 (premium-rate), etc. |

Non-geographic series are identified automatically; **900 numbers trigger a red premium-rate fraud warning**.

Refresh the local database (requires a repo clone):

```bash
python3 tools/update_ift_blocks.py
```

The script downloads the current plan from sns.ift.org.mx and rebuilds the compact lookup files. Use `--offline` to rebuild without downloading.

---

## Optional API Sources

Some features may depend on external API keys.

| Service     | Purpose                                         |
| ----------- | ----------------------------------------------- |
| AbstractAPI | Phone validation and enrichment                 |
| NumVerify   | Secondary phone validation                      |
| Geoapify    | Mexican numbering-locality geocoding           |
| Google Places | Optional public business-listing lookup      |
| IPQualityScore | Optional phone validation and abuse evidence |

MeXiCOSINT can work partially without API keys, but some results may be limited.

---

## Configuration File

The recommended local configuration file is:

```text
~/.mx_osint_config.json
```

This file should exist only on your local machine.

Do not upload it to GitHub.

---

## Creating the Configuration File

Create the file with:

```bash
nano ~/.mx_osint_config.json
```

Example configuration:

```json
{
  "abstractapi_key": "YOUR_ABSTRACTAPI_KEY",
  "numverify_key": "YOUR_NUMVERIFY_KEY",
  "geoapify": "YOUR_GEOAPIFY_KEY",
  "google_places": "YOUR_GOOGLE_PLACES_KEY",
  "ipqualityscore": "YOUR_IPQUALITYSCORE_KEY"
}
```

Replace each placeholder value with your own API key.

---

## Protecting the Configuration File

Apply safer permissions:

```bash
chmod 600 ~/.mx_osint_config.json
```

Check the file permissions:

```bash
ls -la ~/.mx_osint_config.json
```

Expected result should look similar to:

```text
-rw------- 1 user user ... /home/user/.mx_osint_config.json
```

---

## Running Without API Keys

MeXiCOSINT may still work partially without API keys.

Example:

```text
Without API keys:
- Local validation
- Basic parsing
- National and international formatting
- IFT/PNN block lookup (offline, always available)

With API keys:
- Additional enrichment
- Secondary validation
- More source comparison
- Better report context
```

---

## Reports and Generated Files

If the tool generates reports, possible files may include:

```text
report.json
```

```text
report.html
```

```text
report_map.html
```

Actual filenames may change depending on the version.

Possible output folders may include:

```text
reports/
```

```text
output/
```

```text
results/
```

If no report appears, check the terminal output to confirm whether report generation is available in your current version.

---

## Files That Should Not Be Uploaded

Do not upload files containing API keys, tokens, credentials, or sensitive data.

Examples:

```text
.env
*.env
.mx_osint_config.json
config.json
secrets.json
keys.json
tokens.json
credentials.json
```

If one of these files is accidentally uploaded, remove it and rotate the exposed keys.

An API key uploaded to GitHub is basically a free snack for bots. The internet remains a deeply embarrassing ecosystem.

---

## Recommended `.gitignore` Entries

The `.gitignore` file should include entries such as:

```gitignore
.env
*.env
.mx_osint_config.json
config.json
secrets.json
keys.json
tokens.json
credentials.json
*.key
*.pem
```

---

## Checking for Secrets Before Committing

Before pushing changes, search for possible exposed secrets:

```bash
grep -Ri "api_key\|apikey\|token\|secret\|password\|credential" .
```

Check modified files:

```bash
git status
```

Review differences:

```bash
git diff
```

If a real key appears, remove it before committing.

---

## If You Accidentally Uploaded an API Key

1. Remove the key from the repository.
2. Commit the cleanup.
3. Open the API provider dashboard.
4. Revoke or delete the exposed API key.
5. Create a new API key.
6. Update your local `~/.mx_osint_config.json` file.

Deleting the line from the current file is not always enough because Git keeps history. Git is useful, but it is also an obsessive little archivist.

---

## Updating MeXiCOSINT

If installed with pipx:

```bash
pipx upgrade mexicosint
```

If installed with pip:

```bash
pip install --upgrade mexicosint
```

If you cloned the repository:

```bash
git pull
pip install -r requirements.txt
```

---

## Development or Test Mode

If the current version includes a development or dummy test mode, it may be executed with a special flag.

Example:

```bash
PYTHONPATH=src python3 -m mexicosint --dummy-test
```

This mode is intended for local development and testing.

It should not be treated as the main user-facing workflow.

---

## Troubleshooting

### `python3: command not found`

Install Python:

```bash
sudo apt install -y python3
```

---

### `pip: command not found`

Install pip:

```bash
sudo apt install -y python3-pip
```

---

### `pipx: command not found`

Install pipx:

```bash
sudo apt install -y pipx
```

If the `mexicosint` command is missing after a pipx install, fix the PATH:

```bash
pipx ensurepath
```

Close and reopen the terminal afterwards.

---

### `error: externally-managed-environment`

You are trying to use global `pip install` on a PEP 668 system (modern Kali/Debian/Ubuntu). Use `pipx install mexicosint` instead.

---

### Error creating the virtual environment

Install venv:

```bash
sudo apt install -y python3-venv
```

Then recreate the virtual environment:

```bash
python3 -m venv venv
```

---

### `bash bin/mexicosint` does not work

Confirm you are inside the project folder:

```bash
pwd
```

Confirm the launcher exists:

```bash
ls -la bin
```

Run it again:

```bash
bash bin/mexicosint
```

---

### Dependency error

Reinstall the requirements:

```bash
pip install -r requirements.txt
```

---

### Virtual environment problem

Recreate the virtual environment:

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

### API key not detected

Check that the configuration file exists:

```bash
ls -la ~/.mx_osint_config.json
```

Apply safe permissions:

```bash
chmod 600 ~/.mx_osint_config.json
```

Review the configuration guide:

```text
docs/CONFIG.md
```

---

## Security Notes

MeXiCOSINT is intended for authorized research, self-auditing, and educational OSINT workflows.

Do not use this tool for harassment, doxxing, fraud, threats, stalking, or unauthorized activity.

The tool does not guarantee identity, exact location, ownership, or definitive attribution of a phone number.

Results should be verified with more than one source.

---

## Best Practices

* Keep API keys out of the repository.
* Do not hardcode API keys into the source code.
* Do not publish screenshots containing visible keys.
* Use fake placeholder values in public documentation.
* Use `chmod 600` for sensitive local files.
* Rotate any exposed API key.
* Review changes before committing.
* Treat OSINT results as indicators, not proof.

---

## Project Status

This project is under active development.

Planned improvements may include:

* Installable packaging
* Global `mexicosint` command
* GitHub releases
* Local `.deb` package for apt-based installation
* Expanded documentation
* Additional validation and testing
* Improved internal structure

---

## License

This project is released under the license included in the repository.
