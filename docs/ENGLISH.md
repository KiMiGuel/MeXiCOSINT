# MeXiCOSINT English Documentation

**MeXiCOSINT v2.5.0** is a Python OSINT tool focused on Mexican phone-number analysis, validation, enrichment, and reporting.

It is phone-only in v2.5.0. The old IP workflow was removed: no `--ip`, no Shodan, no IPInfo, and no IP2Location.

> Treat results as OSINT indicators, not proof of identity, ownership, live location, or subscriber attribution.

---

## Features

* Mexican phone-number validation.
* National and international formatting.
* Accepted Mexican phone formats: `+526634647308`, `526634647308`, `6634647308`, `+52 663 464 7308`, `52-663-464-7308`, `(663) 464-7308`.
* Official IFT/PNN block lookup, offline.
* LADA reference data as fallback or supporting evidence.
* Canonical locality from IFT/LADA.
* Optional enrichment from AbstractAPI, NumVerify, OpenCage, Geoapify, Google Places, and IPQualityScore.
* OSINT links using exact phone-number variants.
* JSON reports under `output/reports/`.
* CLI API-key management with `--set-key`, `--list-keys`, and `--config-path`.
* `--dummy-test` mode with fixtures and no live API calls.

---

## Installation

Recommended installation with `pipx`:

```bash
sudo apt install -y pipx
pipx install mexicosint
```

Run:

```bash
mexicosint 5512345678
```

Upgrade:

```bash
pipx upgrade mexicosint
```

Direct pip installation:

```bash
pip install mexicosint
```

Repository installation for development:

```bash
git clone https://github.com/KiMiGuel/MeXiCOSINT.git
cd MeXiCOSINT
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

Run from a repository checkout:

```bash
bash bin/mexicosint 5512345678
```

Or run the module directly:

```bash
PYTHONPATH=src python3 -m mexicosint 5512345678
```

---

## Usage

Basic scan:

```bash
mexicosint 5512345678
```

Compact banner:

```bash
mexicosint -b 5512345678
```

Dummy test, with no live API calls:

```bash
mexicosint --dummy-test 6634647308
```

Show version:

```bash
mexicosint --version
```

Show help:

```bash
mexicosint --help
```

Current CLI shape:

```text
mexicosint [-h] [--dummy-test] [-b]
           [--set-key SERVICIO KEY] [--list-keys] [--config-path]
           [--version] [number]
```

---

## API Keys

MeXiCOSINT works without API keys for local validation, IFT/PNN lookup, LADA support, and OSINT links.

Optional providers are used automatically when their key is configured. Missing keys skip only that provider.

Current API-key commands:

```bash
mexicosint --set-key opencage TU_KEY
mexicosint --set-key geoapify TU_KEY
mexicosint --set-key google_places TU_KEY
mexicosint --set-key ipqualityscore TU_KEY
mexicosint --set-key abstract TU_KEY
mexicosint --set-key numverify TU_KEY
```

Valid service names:

```text
abstract
abstract_phone_intelligence
numverify
opencage
geoapify
google_places
ipqualityscore
```

List configured keys, masked:

```bash
mexicosint --list-keys
```

Show the config path:

```bash
mexicosint --config-path
```

Recommended local config path:

```text
~/.mx_osint_config.json
```

Example config with fake placeholders:

```json
{
  "abstract_phone_intelligence": "TU_ABSTRACTAPI_KEY",
  "numverify": "TU_NUMVERIFY_KEY",
  "opencage": "TU_OPENCAGE_KEY",
  "geoapify": "TU_GEOAPIFY_KEY",
  "google_places": "TU_GOOGLE_PLACES_KEY",
  "ipqualityscore": "TU_IPQUALITYSCORE_KEY"
}
```

Protect the file:

```bash
chmod 600 ~/.mx_osint_config.json
```

Do not commit API keys, `.env`, config files, reports with sensitive data, or credentials.

---

## Provider Behavior

| Provider | Role |
|---|---|
| AbstractAPI | Phone validation and enrichment as supporting/conflict evidence |
| NumVerify | Secondary validation as supporting/conflict evidence |
| OpenCage | Primary optional geocoder for canonical IFT/LADA locality |
| Geoapify | Optional geocoder fallback for canonical IFT/LADA locality |
| Google Places | Public business-listing search by normalized E.164 phone number |
| IPQualityScore | Phone validation, reputation, abuse, activity, VoIP, carrier, and line-type evidence |
| Nominatim | Final geocoder fallback when keyed geocoders are unavailable or return no result |

AbstractAPI, NumVerify, and IPQualityScore locality fields do not override concrete IFT/LADA locality.

Google Places searches the normalized E.164 phone number directly, using a spaced search form such as:

```text
+52 664 483 7308
```

IFT/LADA may be used only to validate or region-bias a public business candidate. A Google Places match is not subscriber identity.

---

## IFT/LADA Locality Pipeline

The 2026 IFT block and LADA datasets included in the repository are authoritative for Mexican numbering locality.

Pipeline:

1. Normalize the phone number.
2. Perform exact IFT block lookup.
3. Derive canonical city or municipality and state from IFT.
4. Use LADA mapping only as fallback or supporting evidence.
5. Build one canonical geocoding query:

```text
<city or municipality>, <state>, Mexico
```

6. Use OpenCage first when configured.
7. Use Geoapify as fallback when configured.
8. Use Nominatim as final fallback.

Vague values are never geocoded. Examples of rejected geocoding inputs:

```text
Mexico
NorthWest
country-only values
generic regions
line types
provider labels without concrete city/state
```

Conflicts between sources can be shown, but the canonical locality and source attribution remain clear.

---

## OSINT Links

Generated OSINT links use exact number variants:

* WhatsApp via `wa.me`.
* Google search for E.164.
* Google search for international digits.
* Google search for national digits.
* Google search for spaced phone format.
* Google `site:` searches for Facebook, TikTok, X, and Twitter.
* E.164 format reference.

The complete link set is also stored in the JSON report.

---

## Reports

Reports are written under:

```text
output/reports/
```

Each report is generated from the current scan run and includes a scan ID, provider status, evidence state, normalized number, source attribution, OSINT links, and available provider data.

---

## Updating IFT Data

The package already includes the current data. If you are working from a repository checkout and need to rebuild it:

```bash
python3 tools/update_ift_blocks.py
```

Offline rebuild:

```bash
python3 tools/update_ift_blocks.py --offline
```

Do not replace the refreshed IFT/LADA data with older files.

---

## Security

Never request, display, hardcode, log, or commit an API key.

Do not upload:

```text
.env
*.env
.mx_osint_config.json
config.json
secrets.json
keys.json
tokens.json
credentials.json
output/reports/ with sensitive case data
```

If a key is exposed, revoke it in the provider dashboard and create a new one.

---

## Troubleshooting

Command not found after `pipx` installation:

```bash
pipx ensurepath
```

Then reopen the terminal.

Check installed version:

```bash
mexicosint --version
```

Check configured keys:

```bash
mexicosint --list-keys
```

Run a safe dummy scan:

```bash
mexicosint --dummy-test 6634647308
```

---

## Project Status

MeXiCOSINT v2.5.0 is focused on Mexican phone-number OSINT. It does not perform IP enrichment.

Use it only for authorized research, self-auditing, and educational workflows.
