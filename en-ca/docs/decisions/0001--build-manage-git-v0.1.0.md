---
title: "Decision: Build manage-git"
dc:title: "Decision: Build manage-git"
dc:creator: "Christopher Steel"
dc:contributor: "Claude Opus 5.5 (Anthropic), AI assistance"
dc:subject: "OSAT manager, git, conda-forge, lock files, relocation, baseline contract, platforms"
dc:description: "Build manage-git as an OSAT manager that installs conda-forge's precompiled git on Linux, macOS and Windows from reviewed lock files, and checks any git against a baseline contract for other managers."
dc:date: "2026-10-21"
dc:type: "Text"
dc:format: "text/markdown"
dc:identifier: "urn:uuid:19425b6e-28ad-4d57-b7c1-dd4d56a7c06c"
dc:relation: "urn:uuid:73f941dd-4bde-457e-81b9-9d6447baae54"
dc:language: "en-CA"
dc:rights: "CC-BY-4.0"
sat:version: "0.1.0"
sat:status: "Accepted"
---

# Decision: Build manage-git

Version: 0.1.0
Status: Accepted, on merge of the pull request that introduces it

## Context

Every OSAT manager starts with a decision record naming the managed tool, its radar entry, the platforms targeted first, and anything the manager does differently from the contract <a id="cite-steel-2026a"></a>[(Steel, 2026a)](#ref-steel-2026a). git comes before most other managers because they need it: the 2026-09-30 scoping, kept under `references/`, made osat-manager-git the unified git base that other managers ask whether git is ready.

The project plan in uc-automa <a id="cite-steel-2026b"></a>[(Steel, 2026b)](#ref-steel-2026b) proposed conda-forge for Linux and macOS and MinGit for Windows. Christopher Steel chose on 2026-10-21 to use conda-forge's precompiled git on all three platforms, so the manager has one source kind.

conda-forge publishes git, built from one feedstock <a id="cite-condaforge-nd"></a>[(conda-forge, n.d.)](#ref-condaforge-nd), for `linux-64`, `linux-aarch64`, `osx-64`, `osx-arm64`, `win-64` and `win-arm64`. Read from the channel's `current_repodata.json` and from the `win-64` package, downloaded on 2026-10-21:

- Version 2.56.0, build 0, is current on every subdir.
- Linux and macOS packages are about 12 MB and depend on `libcurl`, `openssl`, `pcre2`, `perl` and others, with build-prefix placeholders that must be rewritten on install.
- Windows packages are about 121 MB, declare no dependencies, and hold 9,612 files under `Library/`, including `Library/cmd/git.exe`. One text file, `Library/etc/profile.d/env.sh`, carries a build-prefix placeholder; no binary does.
- Packages are `.conda` files, a zip holding two zstd-compressed tarballs. Their SHA-256 and size are published in repodata over HTTPS; the packages are not signed.
- The recipe labels git `GPL-2.0-or-later and LGPL-2.1-or-later`. Git itself is `GPL-2.0-only`.

## Decision

Build `manage-git`, meeting the OSAT manager contract, with these choices.

- **Source on every platform:** conda-forge's `git` package, from `https://conda.anaconda.org/conda-forge/`. No system package manager, no MinGit, no dugite-native.
- **Platforms targeted first:** Linux on x86_64 and aarch64, macOS on x86_64 and arm64, Windows on x86_64 and ARM64. None is verified at 0.1.0 until its end-to-end run.
- **A fixed package set per version (D2):** the manager never solves dependencies at run time. For each git version and subdir, a lock file under `locks/<version>/<subdir>.json` lists every package's file name, URL, SHA-256 and size. It is produced at release time by a separate tool allowed more than the standard library, cross-checked against the anaconda.org API, reviewed when it changes, and signed with the release key (uc-automa 0032). The lock is the trust anchor; Sigstore attestations under CEP 27 become required once conda-forge publishes them for every subdir.
- **Reading zstd (D1):** manage-git requires Python 3.14 or later and reads `.conda` files with `compression.zstd` from the standard library. manage-python installs that Python. This differs from the contract's earlier floor of Python 3.8.
- **Relocation:** the manager rewrites prefix placeholders as listed in each package's `info/paths.json`, text by substitution and binary by substitution padded with null bytes, and refuses any package whose `paths.json` it does not fully understand, or whose placeholder is shorter than the install prefix.
- **Re-signing on macOS arm64 (D4):** one named exception to the no-shell-commands rule, `/usr/bin/codesign -s - -f` on files the manager has just patched. Revisited if a standard-library ad hoc signer proves small enough to review.
- **Where the conda logic lives (D3):** it is written as a self-contained `conda` source kind, ready to move into the shared manager package (uc-automa 0024) when that package exists. Until then it lives here, listed as known debt, beside this manager's copies of the YAML subset reader and the data lookup.
- **Windows specifics:** aliases target `Library\cmd\git.exe`, as Git for Windows does for `cmd`. The 9,612-file tree is unpacked below a short install root, because long paths are not assumed. Each version's archive costs about 121 MB.
- **Configuration:** each installed prefix carries a system `gitconfig` that belongs to the manager and holds the baseline settings. The manager never reads configuration from another git installation and never writes to the user's `~/.gitconfig`.
- **CA certificates:** `ca-certificates` is in every Linux and macOS lock, because conda's `openssl` and `libcurl` look for certificates in the prefix. Every end-to-end run clones over HTTPS to prove it.
- **The baseline contract:** `manage-git --check` reports each git it can see, the managed ones and the first on `PATH`, against the baseline in `manager.yaml`: a minimum version and required configuration values. `--json` gives the form other managers read. Checking runs the git binary being checked; nothing else is run.
- **Messages:** every message comes from a catalogue, complete in en-CA and fr-CA (requirement GIT-7).
- **Licence recorded:** `manager.yaml` records git as `GPL-2.0-only`. The conda-forge label is worth reporting to the feedstock.
- **Locations:** the install root is `osat/git` in each platform's per-user data directory, and launchers go where manage-restic puts them, `~/.local/bin` on Linux and macOS and `%LOCALAPPDATA%\osat\bin` on Windows.

## Carried forward from the 2026-09-30 scoping

The baseline contract, the five requirement areas (ID, ML, SEC, AL, GIT) and the en-ca and fr-ca messages stand. Requirements GIT-1, discovering every installation on the machine, and GIT-2, installing through native package managers, do not: the manager reports installations it manages and the first git on `PATH`, and installs only from its locks.

## Consequences

- A new git version reaches users only after conda-forge rebuilds it and a reviewed lock is released.
- Windows users get Git for Windows as repackaged by conda-forge, a link in the chain that MinGit would avoid, in exchange for one source kind and one verification path.
- Perl comes with git on Linux and macOS; dropping it would break `git send-email`, `git svn` and other Perl commands.
- The minimum git version in the baseline is open, proposed as 2.49.0, the oldest version conda-forge lists for every subdir in its current repodata.
- Reaching 1.0.0 needs all three platforms verified (uc-automa 0011).

## References

<a id="ref-condaforge-nd"></a>conda-forge. (n.d.). *git-feedstock* [Computer software]. GitHub. Retrieved October 21, 2026, from https://github.com/conda-forge/git-feedstock [↩](#cite-condaforge-nd)

<a id="ref-steel-2026a"></a>Steel, C. (2026a). *Creating an OSAT manager repository* (Version 0.4.0) [Unpublished manuscript]. uc-automa. urn:uuid:b18e2ed3-b364-4880-b3c7-5676961f0174 [↩](#cite-steel-2026a)

<a id="ref-steel-2026b"></a>Steel, C. (2026b). *osat-manager-git* [Project plan, unpublished manuscript]. uc-automa. urn:uuid:73f941dd-4bde-457e-81b9-9d6447baae54 [↩](#cite-steel-2026b)

## Changelog

| Version | Date | Status | Notes |
| --- | --- | --- | --- |
| 0.1.0 | 2026-10-21 | Accepted | Initial version: conda-forge on all three platforms, D1 to D4 from the project plan |

## License

This document, *Decision: Build manage-git*, by **Christopher Steel**, with AI assistance from **Claude Opus 5.5 (Anthropic)**, is licensed under the [Creative Commons Attribution 4.0 International License](https://creativecommons.org/licenses/by/4.0/).
