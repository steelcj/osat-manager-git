---
title: "Decision: Baseline 1 and Repository Conventions"
dc:title: "Decision: Baseline 1 and Repository Conventions"
dc:creator: "Christopher Steel"
dc:contributor: "Claude Opus 5.5 (Anthropic), AI assistance"
dc:subject: "OSAT manager, git, baseline, exit status, manager.yaml, launchers, uninstall, known debt"
dc:description: "Settles baseline 1, what manage-git's exit status 2 means, the manager.yaml field names used until the shared schema exists, how Windows launchers, a real git.exe and uninstall work, where lock files live, the message catalogues' format, and the YAML reader as known debt."
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

Decision 0001 left the baseline's values as proposals, and the first pull request asked about conventions no uc-automa rule covers. Christopher Steel answered on 2026-10-21: the proposed values stand, `safe.directory` is left out, exit status 2 means "not ready", the copied YAML reader is acceptable debt, restic is not the model git has to follow, and nothing may be left behind on uninstall, with no registry writes. uc-automa 0033 and 0034 were accepted the same day. On the remaining questions, where lock files live, how Windows programs find a real `git.exe`, and the catalogues' format, he asked for the recommended choices.

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

### A real git.exe on Windows

Many Windows programs, such as editors and git-cola, look for `git.exe` and cannot run a `.cmd` alias. mise answers this with a small native shim copied as each command's `.exe`; the standard library cannot build one. manage-git instead:

- keeps a directory junction, `current`, under its install root, pointing at the active version's prefix. A junction needs no administrator rights;
- appends one `[include]` of the manager's system configuration to the end of the Windows package's own `Library/etc/gitconfig`, so a `git.exe` started without `GIT_CONFIG_SYSTEM` still gets the baseline. This is the one change to a delivered file, on Windows only, and the manager records the file's new SHA-256 with the version's provenance. On Linux and macOS the package's file stays as delivered;
- tells the person, once, to add `%LOCALAPPDATA%\osat\git\current\Library\cmd` to their `PATH`, as they already add the alias directory. The manager never changes `PATH` itself.

Switching versions moves the junction. The Windows end-to-end run confirms that git, Git Credential Manager and an editor all work through it.

### Lock files ship with the manager

Locks live in the repository at `locks/<version>/<subdir>.json`, are signed with the release key, and are installed with the manager as package data (uc-automa 0019). A new git version reaches users in a new manage-git release, reviewed with the code. Installing a version needs nothing the manager does not already carry, which also keeps installs working on intermittent networks once the packages are archived.

### Nothing left behind, no registry writes

`--uninstall` removes everything the manager owns and writes nothing to the registry. On Windows, where a running program cannot delete its own files, the last step is a batch file that deletes the remaining directory and then itself. The same applies to manage-python's manager runtime under uc-automa 0033.

### Known debt

The YAML subset reader and the data lookup are copies of osat-manager-restic's, kept until the shared manager package exists, alongside the conda source kind (decision 0001) and the JSON message catalogues.

### Message catalogues follow SAT

Interface messages follow SAT's sidecar specification: gettext catalogues under each language root, `en-ca/messages/LC_MESSAGES/osat-manager-git.po` and `fr-ca/messages/LC_MESSAGES/osat-manager-git.po`, with the template at `lib/locale/osat-manager-git.pot`. Release tooling compiles them to `.mo` files, which the standard library's `gettext` reads, and the wheel carries them. msgmerge and fuzzy matching then handle translation drift, as SAT intends.

The catalogue machinery is the same for every manager, so it is built once, in the shared manager package (uc-automa 0035). Until then the JSON catalogues stay in `lib/osat_manager_git/messages/` as known debt, so they move only once.

## Consequences

- `--check` now requires `credential.helper = manager` on Windows.
- Whoever builds the shared package renames these fields once, in every manager that uses them.
- Releasing a new git version means a manage-git release.
- On Windows, the package's `Library/etc/gitconfig` no longer matches the hash in its lock after install; the recorded provenance hash is what later checks compare against.

## Changelog

| Version | Date | Status | Notes |
| --- | --- | --- | --- |
| 0.1.0 | 2026-10-21 | Accepted | Initial version, from Christopher Steel's answers of 2026-10-21, including the recommended choices for lock files, a real `git.exe` on Windows and message catalogues |

## License

This document, *Decision: Baseline 1 and Repository Conventions*, by **Christopher Steel**, with AI assistance from **Claude Opus 5.5 (Anthropic)**, is licensed under the [Creative Commons Attribution 4.0 International License](https://creativecommons.org/licenses/by/4.0/).
