# Roadmap

Forward plan only; completed items move to [CHANGELOG.md](CHANGELOG.md).

## 0.1.0

- A release-time tool, outside the runtime manager and allowed more than the standard library, that resolves the package set for each git version and subdir into `locks/<version>/<subdir>.json` with rattler or micromamba, then cross-checks every hash and size against the anaconda.org API.
- Locks for git 2.56.0 on all six subdirs, reviewed and signed with the release key.
- Safe unpacking of `.conda` packages: no absolute paths, no `..`, no links that leave the prefix.
- Relocation through `info/paths.json`, text and binary, refusing a placeholder shorter than the install prefix; unit tests against small fake packages.
- Ad hoc re-signing on macOS arm64 through the one named `codesign` exception.
- The contract: install and activate, switch, aliases `git` and `git-{major}.{minor}`, protection, nothing left behind, the verified archive kept with its lock, self-install.
- Write each version's system configuration and launchers on install and switch, and remove them with the version. Rendering both is in place.
- Independent review of the unpacking and relocation code before the tag.
- The end-to-end scenario on Linux amd64, cloning over HTTPS to prove the certificates in the prefix.

## Next release

- End-to-end runs on Linux arm64, Windows x64 and Windows ARM64.
- macOS, on Apple hardware.
- A real `git.exe` on Windows through the `current` junction (decision 0002).

## Later

- Move the conda source kind, the YAML subset reader and the data lookup into osat-manager-core, the shared manager package (uc-automa 0024 and 0035), and switch the message catalogues to its gettext machinery under `en-ca/messages/` and `fr-ca/messages/`.
- Require Sigstore attestations under CEP 27 once conda-forge publishes them for every subdir.
- A git-lfs companion manager from conda-forge.
- Report the licence mislabel to the git-feedstock.
- Reach 1.0.0 when Linux, macOS and Windows are all verified.

## License

This document, *Roadmap*, by **Christopher Steel**, with AI assistance from **Claude Opus 5.5 (Anthropic)**, is licensed under the [Creative Commons Attribution 4.0 International License](https://creativecommons.org/licenses/by/4.0/).
