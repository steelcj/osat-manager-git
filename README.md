# osat-manager-git

`manage-git` installs git into your own account on Linux, macOS and Windows, keeps several versions side by side, and tells other OSAT managers whether git is ready. It uses conda-forge's precompiled git on every platform, installs exactly the packages named in a reviewed lock file, and needs no administrator rights, no system package manager and no compiler. The choices behind it are in [decision 0001](en-ca/docs/decisions/0001--build-manage-git-v0.1.0.md).

## Status

**0.1.0, in development.** `manage-git --check` works: it reports the first git on `PATH`, and every version the manager has installed, against the baseline contract, in English or French, as text or JSON. Installing, switching, aliases, protection, the verified archive and self-install are a skeleton that says so plainly; see [ROADMAP.md](ROADMAP.md).

| Platform | conda-forge subdirs | Status |
| --- | --- | --- |
| Linux | `linux-64`, `linux-aarch64` | Not yet verified |
| macOS | `osx-64`, `osx-arm64` | Not yet verified: no Apple hardware available |
| Windows | `win-64`, `win-arm64` | Not yet verified |

A platform is marked verified only after the end-to-end scenario has run on it.

## Requirements

Python 3.14 or later, which [manage-python](https://github.com/steelcj/osat-manager-python) installs. manage-git reads conda packages with `compression.zstd`, which the standard library gained in 3.14.

## Install

Until the first release is tagged, install from a checkout:

```sh
python3.14 -m pip install --user .
manage-git --check
```

## Checking git

```sh
manage-git --check            # readable report
manage-git --check --json     # what other managers read
manage-git --check --lang fr-ca
```

Exit status 0 means the first git on `PATH` meets the baseline, 2 means it does not, and 1 means the check could not run. The baseline, a minimum version and required configuration, lives in [manager.yaml](manager.yaml). The full command reference is in the [usage guide](en-ca/docs/guides/usage/using-manage-git-v0.1.0.md).

## Documentation

- [Documentation index](en-ca/docs/README.md)
- [Contributing](CONTRIBUTING.md)

## License

Code is under the MIT License, documentation under CC BY 4.0, as [REUSE.toml](REUSE.toml) records. git itself, which this manager installs, is GPL-2.0-only.

This document, *osat-manager-git*, by **Christopher Steel**, with AI assistance from **Claude Opus 5.5 (Anthropic)**, is licensed under the [Creative Commons Attribution 4.0 International License](https://creativecommons.org/licenses/by/4.0/).
