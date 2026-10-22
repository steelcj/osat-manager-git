# osat-manager-git

`manage-git` installs conda-forge's precompiled git into a user's own account and manages its versions, and checks any git against the baseline contract other managers rely on. Decision 0001 sets out how.

## Working here

- Standard library only, `pathlib` throughout, Python 3.14 or later. The manager runs only the git it is checking, and on macOS arm64 the one named `codesign` exception; never a shell. Tests may use more.
- Platform differences live in `lib/osat_manager_git/platforms.py` and nowhere else.
- Never weaken verification: a package is unpacked only after its size and SHA-256 match its lock, and the manager never solves dependencies at run time.
- Every message goes through the catalogues; en-ca and fr-ca stay complete.
- Run `python3.14 -m unittest discover -s tests/unit` and `uc-automa check` before committing.
- A platform is verified only by running the end-to-end scenario on it; never claim one that has not been run.
- Ask before pushing, tagging, or using any test machine.

<!-- uc-portage:begin uc-automa-signpost -->
## uc-automa

This repository follows uc-automa at the version pinned in `.uc-automa.yaml`.

- The rules are uc-automa's directives, under `en-ca/docs/directives/` at that version. Each names the check that enforces it, if it has one.
- Run `uc-automa check` before committing, and `uc-automa offerings plan` to see whether shared files have drifted.
- Files the layout marks `from_offering` arrive from uc-automa; change them there, not here.
- If a rule is not written in a directive, ask. Never copy a convention from another repository.
<!-- uc-portage:end uc-automa-signpost -->
