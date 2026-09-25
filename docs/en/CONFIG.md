# Configuration and credentials

MeXiCOSINT uses **MicroVault as the only credential backend** for normal
provider enrichment.

## Credential contract

- Normal scans require the MicroVault profile named `mexicosint`.
- MeXiCOSINT queries that profile through the local bridge and the command
  `microvault env --profile mexicosint --json`.
- There is no fallback to a full vault, individual services, generic
  environment variables, or JSON files.
- MeXiCOSINT does not create, read, or write credential configuration files.
- The master password is requested by MicroVault in an interactive terminal.
- Dummy mode is the only exception: it uses in-memory fixtures and consumes
  no credentials.

## Configure the profile

In MicroVault, save the credentials you want to use and create the profile:

```bash
microvault profile mexicosint geoapify opencage_api ipgs numverify_api abstract_api verificaremails
```

The service names MeXiCOSINT expects are:

| MeXiCOSINT service | MicroVault name |
|---|---|
| AbstractAPI | `abstract_api` |
| NumVerify | `numverify_api` |
| OpenCage | `opencage_api` |
| Geoapify | `geoapify` |
| IPQualityScore | `ipgs` |
| Verificar Emails | `verificaremails` |

Then run normally:

```bash
mexicosint 5512345678
```

Configuration of these credentials happens exclusively in MicroVault;
MeXiCOSINT offers no commands to save or list keys.

## Run options

`--microvault` forces the required profile connection. There is no alternate
credential path; normal scans use the MicroVault profile, while dummy mode
uses in-memory fixtures.

## Security

Never save keys in the repository or include them in logs, reports, or
examples. If a credential is exposed, revoke it at the provider and replace
it in MicroVault.

To check for secrets before committing:

```bash
grep -RiE "api[_-]?key|token|secret|password|credential" .
```

## Provider states

`CONFIGURED_UNVERIFIED` means the profile supplied a key, but it hasn't been
validated against the provider yet. `MISSING` means the profile didn't
supply that key. The reported source is `microvault` or `dummy`; environment
variables and JSON are never reported as a source.
