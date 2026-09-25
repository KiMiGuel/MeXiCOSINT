# Usage guide

## Scan

```bash
mexicosint 5512345678
mexicosint +525512345678
mexicosint "52-663-464-7308"
```

Numbers are normalized and validated; optional providers are only queried
when the MicroVault `mexicosint` profile supplies their credential.

## Options

```text
mexicosint [-h] [--batch FILE] [--diff BEFORE AFTER] [--mexico-only] [--microvault] [--version] [number]
```

| Option | Description |
|---|---|
| `number` | Mexican phone number to scan |
| `--batch FILE` | Processes a file with one number per line and generates a JSON manifest + CSV |
| `--diff BEFORE AFTER` | Compares evidence fields between two JSON reports |
| `--mexico-only` | Skips external phone providers; keeps IFT/PNN and approximate geocoding |
| `--microvault` | Forces the connection to the `mexicosint` profile |
| `--version` | Shows the installed version |
| `-h`, `--help` | Shows help |

MeXiCOSINT has no options to create, save, or list keys: that configuration
lives in MicroVault.

## Credential configuration

```bash
microvault profile mexicosint geoapify opencage_api ipgs numverify_api abstract_api verificaremails
```

The bridge queries this once:

```bash
microvault env --profile mexicosint --json
```

There is no fallback to `microvault env`, `microvault env <service>`, generic
environment variables, or JSON files. If the profile, MicroVault, or the
password prompt is missing, remote enrichment is skipped; use `--microvault`
to make the scan fail loudly on a connection problem.

## Dummy mode

The internal `--dummy-test` flag uses in-memory fixtures and requires no
MicroVault, environment variables, or credential files.

## Features and providers

- Local validation, formatting, and analysis.
- Official offline IFT/PNN and LADA database.
- OSINT links.
- Optional enrichment from AbstractAPI, NumVerify, IPQualityScore.
- Verificar Emails (HLR) as a secondary, optional phone provider.
- OpenCage and Geoapify for concrete locality.
- Nominatim as the final credential-free geocoder.

## Security

Do not upload credentials, `.env`, JSON files, sensitive reports, or
screenshots that contain them. MeXiCOSINT does not create or modify JSON
configuration files. If a credential was exposed, revoke it at the provider
and replace it in MicroVault.

## Troubleshooting

### API enrichment not available

Check that MicroVault is installed, that the profile exists, and that the
command runs from an interactive terminal:

```bash
microvault profile
mexicosint --microvault 5512345678
```

### IFT database doesn't show up

The database ships bundled. To regenerate it:

```bash
python3 tools/update_ift_blocks.py --offline
```
