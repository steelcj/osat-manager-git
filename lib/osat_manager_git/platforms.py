"""Everything that differs between Linux, macOS and Windows, in one place:
which conda subdir to install from, where things are installed, where git
lives inside a prefix, and how installed files are protected."""

from __future__ import annotations

import os
import platform
import re
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Optional

from .errors import ManagerError

SYSTEMS = {"Linux": "linux", "Darwin": "macos", "Windows": "windows"}
HOME_VAR = "OSAT_GIT_HOME"            # overrides the install root
BIN_VAR = "OSAT_BIN_DIR"              # overrides the alias directory
WINDOWS_VAR = re.compile(r"%([A-Za-z0-9_]+)%")


def current_system(name: Optional[str] = None) -> str:
    name = name or platform.system()
    system = SYSTEMS.get(name)
    if system is None:
        raise ManagerError("unsupported_system", system=name)
    return system


def conda_subdir(manifest: dict, system: str,
                 machine: Optional[str] = None) -> str:
    """The conda-forge subdir, such as ``linux-64``, for this machine."""
    machine = machine or platform.machine()
    subdirs = manifest["platforms"][system]["subdir"]
    if machine not in subdirs:
        raise ManagerError("unsupported_arch", system=system, machine=machine,
                           known=", ".join(sorted(subdirs)))
    return subdirs[machine]


def expand(text: str, environ: Mapping[str, str]) -> Path:
    def var(match):
        name = match.group(1)
        if name not in environ:
            raise ManagerError(f"%{name}% is not set")
        return environ[name]
    text = WINDOWS_VAR.sub(var, text)
    if text.startswith("~"):
        home = environ.get("HOME") or environ.get("USERPROFILE")
        text = (home or str(Path.home())) + text[1:]
    return Path(text)


@dataclass
class Paths:
    root: Path
    bin_dir: Path
    executable: str
    windows: bool

    @property
    def versions(self) -> Path:
        return self.root / "versions"

    @property
    def archive(self) -> Path:
        return self.root / "archive"

    @property
    def staging(self) -> Path:
        return self.root / "staging"

    @property
    def manager(self) -> Path:
        return self.root / "manager"

    @property
    def state(self) -> Path:
        return self.root / "state.json"

    def prefix(self, version: str) -> Path:
        """The conda prefix one git version is unpacked into."""
        return self.versions / version

    def git(self, version: str) -> Path:
        return self.prefix(version) / Path(*self.executable.split("/"))

    def launcher(self, name: str) -> Path:
        return self.bin_dir / (f"{name}.cmd" if self.windows else name)


def resolve_paths(manifest: dict, system: str,
                  environ: Mapping[str, str] = os.environ) -> Paths:
    root = environ.get(HOME_VAR) or None
    bin_dir = environ.get(BIN_VAR) or None
    root_path = Path(root) if root else expand(manifest["install_root"][system],
                                               environ)
    bin_path = Path(bin_dir) if bin_dir else expand(manifest["bin_dir"][system],
                                                    environ)
    return Paths(root_path, bin_path,
                 manifest["platforms"][system]["executable"],
                 system == "windows")


def baseline_config(manifest: dict, system: str) -> dict:
    """The configuration the baseline requires on this platform."""
    baseline = manifest["baseline"]
    config = dict(baseline.get("config") or {})
    config.update(baseline.get(f"config_{system}") or {})
    return config


# ── Protection ──────────────────────────────────────────────────────────────

def protect(path: Path) -> None:
    """Make an installed file or directory tree read-only."""
    for item in sorted(path.rglob("*"), reverse=True) if path.is_dir() else []:
        _read_only(item)
    _read_only(path)


def _read_only(path: Path) -> None:
    """Owner-only and read-only: 0o500 for directories and executables,
    0o400 for other files. On Windows, the read-only attribute."""
    if os.name == "nt":
        if path.is_file():
            path.chmod(stat.S_IREAD)
        return
    if path.is_symlink():
        return
    executable = path.is_dir() or path.stat().st_mode & stat.S_IXUSR
    path.chmod(0o500 if executable else 0o400)


def unprotect(path: Path) -> None:
    """Make a protected tree writable again, so the manager can remove it."""
    if not path.exists():
        return
    items = [path] + (sorted(path.rglob("*")) if path.is_dir() else [])
    for item in items:
        if item.is_symlink():
            continue
        mode = item.stat().st_mode
        item.chmod(mode | stat.S_IWRITE | stat.S_IREAD |
                   (stat.S_IEXEC if item.is_dir() else 0))
