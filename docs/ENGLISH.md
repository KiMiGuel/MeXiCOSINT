# MeXiCOSINT English Documentation

MeXiCOSINT is a phone-number OSINT tool for Mexican numbers.

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
pip install -r requirements.txt
pip install -e .
bash bin/mexicosint 5512345678
```

## Usage

```text
mexicosint [-h] [--microvault] [--version] [number]
```

- `--microvault` forces the required profile connection.
- `--version` prints the version.
- `--dummy-test` is an internal fixture mode and requires no credentials.

The CLI intentionally has no `--set-key`, `--list-keys`, or `--config-path`
options. Manage credentials in MicroVault:

```bash
microvault profile mexicosint geoapify opencage_api ipgs numverify_api abstract_api
```

## Providers

Optional providers are AbstractAPI, NumVerify, OpenCage, Geoapify, and
IPQualityScore. Offline validation, IFT/PNN, LADA, OSINT links, and
Nominatim remain available when enrichment is skipped.

## Security

Never commit `.env`, JSON credentials, secrets, or sensitive reports. If a key
is exposed, revoke it at the provider and replace it in MicroVault.

## Status

```bash
mexicosint --version
mexicosint 5512345678
```
