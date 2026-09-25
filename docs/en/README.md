# MeXiCOSINT — English Documentation

MeXiCOSINT is an OSINT tool focused on analysis, validation, enrichment, and
reporting for Mexican phone numbers.

> This project is in beta. Results should be treated as OSINT indicators, not
> as absolute evidence.

This page is the English entry point. Full guides:

| Guide | Description |
|---|---|
| [Installation guide](INSTALL.md) | Install instructions for Kali, Debian, Ubuntu, and similar systems |
| [Usage guide](USAGE.md) | Full usage: options, examples, IFT database, API keys |
| [Configuration guide](CONFIG.md) | Local configuration and API key management |

The canonical, most complete documentation is in Spanish: [README](../../README.md),
[docs/INSTALL.md](../INSTALL.md), [docs/USAGE.md](../USAGE.md), [docs/CONFIG.md](../CONFIG.md).
This English set mirrors them and is kept in sync with the same feature set.

## Features

- Mexican phone number validation
- National and international formatting
- Local analysis of Mexican numbers
- Optional enrichment via external APIs
- IFT/SNS-related processing
- OSINT searches via public links for WhatsApp and social networks
- **Official IFT/PNN database built in**: 177k+ assigned numbering blocks, offline lookup
- Carrier, modality, and assignment date straight from the regulator
- Canonical IFT/LADA locality: exact IFT block as the primary source, LADA as backup/support
- Non-geographic series 200/300/500/800/900 with a premium-number (900) alert
- Structured per-provider state: `missing`, `not_requested`, `configured_unverified`, `request_success`, `no_result`, `auth_failed`, `quota_exceeded`, and more
- Selected geocoding source visible in the result
- **MicroVault as the only credential backend** for normal enrichment; requires the `mexicosint` profile
- **Mexico-first model**: IFT/PNN is the primary source for Mexican numbering blocks; Abstract, NumVerify, IPQualityScore, and Verificar Emails (HLR) appear as secondary corroboration and never replace official data
- **Confidence matrix**: the report identifies which fields come from IFT/PNN and which are secondary signals
- Concurrent performance: parallel API calls (asyncio + aiohttp), HTTPS connection pooling, and memoization of normalization and geocoding
- Batch mode, JSON/CSV export, scan history, and evidence diff between two reports
- Phone-only mode: no IP providers or IP scanning

## Credential contract

Normal provider enrichment uses **MicroVault only**. MeXiCOSINT requires the
`mexicosint` profile and fetches it through the local bridge with:

```bash
microvault env --profile mexicosint --json
```

Generic environment variables, plaintext JSON, bare MicroVault output, and
per-service MicroVault requests are not credential sources. MeXiCOSINT does
not create, read, or write credential JSON files. Dummy mode is the only
fixture-based exception.

## Installation

```bash
sudo apt install -y pipx
pipx install mexicosint
mexicosint 5512345678
```

From a checkout:

```bash
git clone https://github.com/KiMiGuel/MeXiCOSINT.git
cd MeXiCOSINT
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .
bash bin/mexicosint 5512345678
```

See [INSTALL.md](INSTALL.md) for update and troubleshooting steps.

## Usage

```text
mexicosint [-h] [--batch FILE] [--diff BEFORE AFTER] [--mexico-only] [--microvault] [--version] [number]
```

- `--batch FILE` processes a file with one number per line and writes a JSON manifest plus a CSV summary.
- `--diff BEFORE AFTER` compares evidence fields between two JSON reports.
- `--mexico-only` skips external phone providers (Abstract, NumVerify, IPQualityScore) while keeping IFT/PNN and approximate geocoding.
- `--microvault` forces the required profile connection.
- `--version` prints the version.
- `--dummy-test` is an internal fixture mode and requires no credentials.

The CLI intentionally has no `--set-key`, `--list-keys`, or `--config-path`
options. Manage credentials in MicroVault:

```bash
microvault profile mexicosint geoapify opencage_api ipgs numverify_api abstract_api verificaremails
```

See [USAGE.md](USAGE.md) for the full option table and troubleshooting.

## Providers

Optional providers are AbstractAPI, NumVerify, OpenCage, Geoapify,
IPQualityScore, and Verificar Emails (HLR, secondary and optional). Offline
validation, IFT/PNN, LADA, OSINT links, and Nominatim remain available when
enrichment is skipped.

## Security

Never commit `.env`, JSON credentials, secrets, or sensitive reports. If a key
is exposed, revoke it at the provider and replace it in MicroVault.

## Disclaimer

MeXiCOSINT is designed for authorized research, self-audits, and educational
OSINT workflows. Do not use it for harassment, doxxing, fraud, threats, or any
unauthorized activity. It does not guarantee identity, exact location,
ownership, or definitive attribution of a phone number.

## Status

```bash
mexicosint --version
mexicosint 5512345678
```
