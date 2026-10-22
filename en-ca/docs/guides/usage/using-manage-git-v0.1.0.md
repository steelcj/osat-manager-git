---
title: "Using manage-git"
dc:title: "Using manage-git"
dc:creator: "Christopher Steel"
dc:contributor: "Claude Opus 5.5 (Anthropic), AI assistance"
dc:subject: "manage-git, git, baseline contract, conda-forge, command reference"
dc:description: "Every manage-git command with examples, what the baseline check reports and how other managers read it, and which commands are not yet implemented at 0.1.0."
dc:date: "2026-10-21"
dc:type: "Text"
dc:format: "text/markdown"
dc:identifier: "urn:uuid:8e4b18f5-b43a-4808-8e7d-4bb124a5be38"
dc:language: "en-CA"
dc:rights: "CC-BY-4.0"
sat:version: "0.1.0"
sat:status: "Accepted"
---

# Using manage-git

Version: 0.1.0
Status: Accepted

## Summary

`manage-git` installs git from conda-forge into your own account and checks whether git is ready for the other OSAT managers. At 0.1.0 only the check works; every other command says it is not implemented yet and exits with status 1. The design is in [decision 0001](../../decisions/0001--build-manage-git-v0.1.0.md).

## Commands

| Command | What it does | At 0.1.0 |
| --- | --- | --- |
| `manage-git --check [--json]` | Check git against the baseline contract | Works |
| `manage-git --install [VERSION]` | Install a locked version, verified, and make it active | Not yet |
| `manage-git --switch VERSION` | Make an installed version active | Not yet |
| `manage-git --status` | Show active, installed and archived versions and aliases | Not yet |
| `manage-git --remove VERSION` | Remove an installed version; its verified archive is kept | Not yet |
| `manage-git --alias OLD=NEW` | Rename an alias | Not yet |
| `manage-git --self-install` | Install the manager itself | Not yet |
| `manage-git --uninstall [--yes]` | Remove everything the manager owns | Not yet |
| `manage-git --version` | Show the manager's version | Works |

`--lang en-ca` or `--lang fr-ca` chooses the language of every message. Without it, manage-git reads `OSAT_LANG`, then the locale variables, and falls back to English.

## Checking git

The check looks at the first git on `PATH` and at every version manage-git has installed. For each it reports the version and compares it, and the configuration git reports from a fresh empty directory, with the baseline in `manager.yaml`.

```sh
$ manage-git --check
Baseline 1: git 2.49.0 or later, with the required configuration
/usr/bin/git (first on PATH): 2.43.0
  version 2.43.0 is older than the baseline minimum 2.49.0
Not ready: the first git on PATH does not meet the baseline
```

| Exit status | Meaning |
| --- | --- |
| 0 | The first git on `PATH` meets the baseline |
| 1 | The check could not run, for example as root or with no `manager.yaml` |
| 2 | The first git on `PATH` does not meet the baseline, or there is none |

## Reading the check from another manager

`--json` prints one object. Other managers read `ready`, and use each problem's `code` and fields rather than its `message`, which is in the caller's language.

```json
{
  "baseline": 1,
  "minimum_version": "2.49.0",
  "ready": false,
  "installations": [
    {
      "path": "/usr/bin/git",
      "origin": "path",
      "version": "2.43.0",
      "meets": false,
      "problems": [
        {"code": "problem_version_too_old", "found": "2.43.0",
         "minimum": "2.49.0", "message": "version 2.43.0 is older than the baseline minimum 2.49.0"}
      ]
    }
  ]
}
```

`origin` is `path` for the first git on `PATH` and `managed` for a version manage-git installed. The problem codes are `problem_version_unreadable`, `problem_version_too_old`, `problem_config_missing` and `problem_config_wrong`.

## The baseline

The baseline is the `baseline` section of `manager.yaml`: a version number for the baseline itself, the minimum git version, the configuration required on every platform, the configuration added on one platform such as `config_windows`, and `unset_means`, git's own default for a key that is not set. A key that is not set but already behaves as required is not reported. Changing these values changes what the check reports, with no code change.

## Environment variables

| Variable | Effect |
| --- | --- |
| `OSAT_GIT_HOME` | Overrides the install root, `osat/git` in the per-user data directory |
| `OSAT_BIN_DIR` | Overrides where launchers go |
| `OSAT_LANG` | Chooses the message language when `--lang` is not given |

## Changelog

| Version | Date | Status | Notes |
| --- | --- | --- | --- |
| 0.1.0 | 2026-10-21 | Accepted | Initial version, for the 0.1.0 skeleton |

## License

This document, *Using manage-git*, by **Christopher Steel**, with AI assistance from **Claude Opus 5.5 (Anthropic)**, is licensed under the [Creative Commons Attribution 4.0 International License](https://creativecommons.org/licenses/by/4.0/).
