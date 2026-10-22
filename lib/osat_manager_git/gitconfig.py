"""The manager-owned system configuration, and how git is started with it
(decision 0001, "Configuration").

A conda-forge git package carries its own system configuration file. On
Linux and macOS, ``etc/gitconfig`` points ``http.sslCAInfo`` at the
prefix's certificate bundle; on Windows, ``Library/etc/gitconfig`` is Git
for Windows' own, with ``core.autocrlf = true``, a required LFS filter and
``credential.helper = helper-selector``. That file stays exactly as the
lock delivered it.

For each installed version the manager writes its own file instead. It
includes the package's file first and then sets the baseline, so the
baseline wins wherever the two disagree. git reads it in place of the
package's file through ``GIT_CONFIG_SYSTEM``, which:

- launchers set, for people and shells (rendered in platforms.py,
  since they differ by platform);
- ``manage-git --check --json`` reports per installation, so other
  managers start the git executable directly with an argument list and
  that one variable, never through a launcher.

Nothing here runs anything; it renders text and writes files.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Mapping, Optional

from .errors import ManagerError

ENV_VAR = "GIT_CONFIG_SYSTEM"

# Keys git treats as lists, where a later value adds to the list instead
# of replacing it. An empty value first resets the list, so the baseline's
# value replaces whatever the package's file set.
MULTI_VALUED = frozenset({"credential.helper"})

HEADER = ("# Written by manage-git: the system configuration for one managed\n"
          "# git version. It includes the package's own file, then sets the\n"
          "# baseline, which wins. Changes here are overwritten; set personal\n"
          "# values in ~/.gitconfig instead.\n")


@dataclass(frozen=True)
class Invocation:
    """How to start one managed git: the executable, and the environment
    to add to the caller's own."""
    executable: str
    env: Dict[str, str] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {"executable": self.executable, "env": dict(self.env)}


def _git_path(path: Path) -> str:
    """A path as a quoted git configuration value. Forward slashes work on
    every platform git runs on, and avoid backslash escapes."""
    text = str(path).replace("\\", "/")
    _refuse_control(text, path)
    return '"' + text.replace('"', '\\"') + '"'


def _value(text: str) -> str:
    _refuse_control(text, text)
    if text == "":
        return ""
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _refuse_control(text: str, shown: object) -> None:
    if any(ord(c) < 0x20 for c in text):
        raise ManagerError("config_value_invalid", value=str(shown))


def _split_key(key: str):
    """``core.autocrlf`` → (``core``, None, ``autocrlf``);
    ``filter.lfs.required`` → (``filter``, ``lfs``, ``required``)."""
    first, _, rest = key.partition(".")
    subsection, _, name = rest.rpartition(".")
    if not first or not name or not first.replace("-", "").isalnum() \
            or not name.replace("-", "").isalnum():
        raise ManagerError("config_key_invalid", key=key)
    return first, (subsection or None), name


def render_system_config(package_config: Optional[Path],
                         settings: Mapping[str, str]) -> str:
    """The text of the manager's file: an include of the package's file,
    when it has one, then each baseline setting, grouped by section in the
    order first seen."""
    lines = [HEADER]
    if package_config is not None:
        lines.append(f"[include]\n\tpath = {_git_path(package_config)}\n")
    sections: Dict[tuple, list] = {}
    for key, value in settings.items():
        section, subsection, name = _split_key(key)
        entries = sections.setdefault((section, subsection), [])
        if key.lower() in MULTI_VALUED:
            entries.append(f"\t{name} =")
        entries.append(f"\t{name} = {_value(value)}")
    for (section, subsection), entries in sections.items():
        if subsection is None:
            header = f"[{section}]"
        else:
            if '"' in subsection or "\\" in subsection:
                raise ManagerError("config_key_invalid",
                                   key=f"{section}.{subsection}")
            header = f'[{section} "{subsection}"]'
        lines.append(header + "\n" + "\n".join(entries) + "\n")
    return "".join(lines)


def write_text(path: Path, text: str, newline: str = "\n") -> None:
    """Write through a temporary file and replace, so a reader never sees
    a half-written file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w", encoding="utf-8", newline=newline) as handle:
        handle.write(text)
    os.replace(temporary, path)
