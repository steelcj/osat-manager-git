---
title: "Decision: Baseline 1 and Repository Conventions"
dc:title: "Decision: Baseline 1 and Repository Conventions"
dc:creator: "Christopher Steel"
dc:contributor: "Claude Opus 5.5 (Anthropic), AI assistance"
dc:subject: "OSAT manager, git, baseline, exit status, manager.yaml, launchers, uninstall, known debt"
dc:description: "Settles baseline 1, what manage-git's exit status 2 means, the manager.yaml field names used until the shared schema exists, how Windows launchers and uninstall work, and the YAML reader as known debt; lock file location and the message catalogues' format stay open."
dc:date: "2026-10-21"
dc:type: "Text"
dc:format: "text/markdown"
dc:identifier: "urn:uuid:46a5763b-3757-45e8-9213-ef016b8922f1"
dc:relation: "urn:uuid:19425b6e-28ad-4d57-b7c1-dd4d56a7c06c"
dc:language: "en-CA"
dc:rights: "CC-BY-4.0"
sat:version: "0.1.0"
sat:status: "Accepted"
---

# Decision: Baseline 1 and Repository Conventions

Version: 0.1.0
Status: Accepted, on merge of the pull request that introduces it

## Context

Decision 0001 left the baseline's values as proposals, and the first pull request asked about conventions no uc-automa rule covers. Christopher Steel answered on 2026-10-21: the proposed values stand, `safe.directory` is left out, exit status 2 means "not ready", the copied YAML reader is acceptable debt, restic is not the model git has to follow, and nothing may be left behind on uninstall, with no registry writes. uc-automa 0033 and 0034 were accepted the same day.

## Decision

### Baseline 1

| Setting | Platforms | Value | Why |
| --- | --- | --- | --- |
| Minimum version | All | 2.49.0 | The oldest version conda-forge lists for every subdir in its current repodata, so the manager can always install one that passes |
| `core.autocrlf` | All | `false` | Line endings belong to each repository's `.gitattributes`, not to the machine |
| `core.longpaths` | Windows | `true` | The Windows package holds 9,612 files, and repositories may be deeper still |
| `credential.helper` | Windows | `manager` | Git Credential Manager, which the package ships, in place of `helper-selector`, which asks through a dialog |

- On Linux and macOS the baseline sets no credential helper; that choice belongs to the person.
- `safe.directory` is not set. Setting it broadly would switch off a protection git added on purpose against repositories owned by someone else.
- The values live in `manager.yaml`, and the manager's per-version system configuration sets them (decision 0001). A person's own `~/.gitconfig` still overrides them; `--check` reports the difference rather than hiding it.

### Exit status

`manage-git --check` exits 0 when the first git on `PATH` meets the baseline, 2 when it does not or there is none, and 1 when the check could not run. Status 2 means "not ready", and is proposed to uc-automa as the meaning for every OSAT manager's check.

### manager.yaml field names

Until the shared manager package defines one schema (uc-automa 0024 and 0034), `manager.yaml` uses:

- `sources.kind: "conda"`, naming the source kind;
- `platforms.<system>.arch`, mapping each machine architecture to what the source needs, here a conda subdir;
- `verification.signature`, whether the trust anchor must be signed, and `verification.signed`, what the anchor is, here the lock file.

These names are provisional; they move to the shared schema when it exists. Lock files keep conda's own word, `subdir`, because they record conda's data.

### Windows launchers

restic's launchers are not the model for git's. A git alias on Windows sets `GIT_CONFIG_SYSTEM` inside `setlocal` and runs `Library\cmd\git.exe`, then exits with its status. Deleting a git alias while git is running from it is not supported. The Windows end-to-end run confirms the form.

### Nothing left behind, no registry writes

`--uninstall` removes everything the manager owns and writes nothing to the registry. On Windows, where a running program cannot delete its own files, the last step is a batch file that deletes the remaining directory and then itself. The same applies to manage-python's manager runtime under uc-automa 0033.

### Known debt

The YAML subset reader and the data lookup are copies of osat-manager-restic's, kept until the shared manager package exists, alongside the conda source kind (decision 0001).

## Open

- **Where lock files live.** Decision 0001 proposed `locks/<version>/<subdir>.json` at the repository root, shipped with the manager as package data, so a new git version arrives with a new manager release.
- **The message catalogues.** They move to the language roots, `en-ca/messages/` and `fr-ca/messages/`, the directory name SAT's sidecar specification uses for interface translations. Whether they stay JSON or become gettext catalogues, which the standard library reads only once compiled, is not settled, so they stay in `lib/osat_manager_git/messages/` until it is.

## Consequences

- `--check` now requires `credential.helper = manager` on Windows.
- Whoever builds the shared package renames these fields once, in every manager that uses them.

## Changelog

| Version | Date | Status | Notes |
| --- | --- | --- | --- |
| 0.1.0 | 2026-10-21 | Accepted | Initial version, from Christopher Steel's answers of 2026-10-21 |

## License

This document, *Decision: Baseline 1 and Repository Conventions*, by **Christopher Steel**, with AI assistance from **Claude Opus 5.5 (Anthropic)**, is licensed under the [Creative Commons Attribution 4.0 International License](https://creativecommons.org/licenses/by/4.0/).
