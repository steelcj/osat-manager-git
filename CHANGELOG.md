# Changelog

All notable changes are recorded here, in the form of [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). This repository follows [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- `manage-git --check`, reporting the first git on `PATH` and every managed version against the baseline in `manager.yaml`, as text or JSON, in en-CA and fr-CA.
- `manager.yaml`, describing conda-forge as the source on Linux, macOS and Windows, the lock file per version and subdir, install locations and the baseline.
- Lock file parsing, size and SHA-256 verification, and reading `info/index.json` and `info/paths.json` from `.conda` packages.
- Decision 0001, *Build manage-git*.
- Decision 0002, *Baseline 1 and Repository Conventions*: baseline 1 confirmed, with Git Credential Manager as the Windows credential helper; exit status 2 means not ready; `manager.yaml` uses `arch` and `verification.signature` and `signed`.
- The manager-owned system configuration: rendering a per-version file that includes the package's own and sets the baseline, read through `GIT_CONFIG_SYSTEM`, and launchers that set it. `--check --json` reports each managed installation's `invocation`, and checks it that way.
- The 2026-09-30 scoping drafts, kept as superseded references.
