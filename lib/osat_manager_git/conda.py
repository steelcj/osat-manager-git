"""The conda source kind: lock files, verified downloads, and reading
``.conda`` packages with the standard library (decision 0001).

Written to move, as one module, into the shared manager package
(uc-automa 0024) once it exists; nothing here is specific to git.

A lock file names, for one tool version and one conda subdir, every
package to install into one prefix:

    {
      "format": 1,
      "tool": "git",
      "version": "2.56.0",
      "subdir": "win-64",
      "channel": "https://conda.anaconda.org/conda-forge",
      "packages": [
        {"name": "git", "version": "2.56.0", "build": "h57928b3_0",
         "subdir": "win-64", "file": "git-2.56.0-h57928b3_0.conda",
         "url": "https://conda.anaconda.org/conda-forge/win-64/git-2.56.0-h57928b3_0.conda",
         "sha256": "908bc78b...", "size": 120811595}
      ]
    }

Each package's ``subdir`` is the lock's subdir or ``noarch``, and its URL
is exactly the channel, that subdir and the file name. Anything else is
refused rather than interpreted.
"""

from __future__ import annotations

import hashlib
import io
import json
import re
import sys
import tarfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from .errors import ManagerError

SHA256 = re.compile(r"^[0-9a-f]{64}$")
FILE = re.compile(r"^[A-Za-z0-9_.+-]+\.conda$")
NAME = re.compile(r"^[a-z0-9][a-z0-9_.+-]*$")
PACKAGE_KEYS = {"name", "version", "build", "subdir", "file", "url", "sha256",
                "size"}
LOCK_KEYS = {"format", "tool", "version", "subdir", "channel", "packages"}
CHUNK = 1 << 20


@dataclass(frozen=True)
class LockedPackage:
    name: str
    version: str
    build: str
    subdir: str
    file: str
    url: str
    sha256: str
    size: int


@dataclass(frozen=True)
class Lock:
    tool: str
    version: str
    subdir: str
    channel: str
    packages: List[LockedPackage]


# ── Lock files ──────────────────────────────────────────────────────────────

def parse_lock(data: object, where: str = "lock") -> Lock:
    def bad(reason: str) -> ManagerError:
        return ManagerError("lock_invalid", path=where, reason=reason)

    if not isinstance(data, dict) or set(data) != LOCK_KEYS:
        raise bad(f"top-level keys must be exactly {sorted(LOCK_KEYS)}")
    if data["format"] != 1:
        raise bad("format must be 1")
    for key in ("tool", "version", "subdir", "channel"):
        if not isinstance(data[key], str) or not data[key]:
            raise bad(f"{key} must be a non-empty string")
    channel = data["channel"]
    if not channel.startswith("https://") or channel.endswith("/"):
        raise bad("channel must be an https URL without a trailing slash")
    if not isinstance(data["packages"], list) or not data["packages"]:
        raise bad("packages must be a non-empty list")

    packages, names = [], set()
    for i, raw in enumerate(data["packages"]):
        if not isinstance(raw, dict) or set(raw) != PACKAGE_KEYS:
            raise bad(f"package {i}: keys must be exactly "
                      f"{sorted(PACKAGE_KEYS)}")
        if not isinstance(raw["size"], int) or isinstance(raw["size"], bool) \
                or raw["size"] <= 0:
            raise bad(f"package {i}: size must be a positive integer")
        for key in PACKAGE_KEYS - {"size"}:
            if not isinstance(raw[key], str) or not raw[key]:
                raise bad(f"package {i}: {key} must be a non-empty string")
        if not NAME.match(raw["name"]):
            raise bad(f"package {i}: invalid name {raw['name']!r}")
        if raw["name"] in names:
            raise bad(f"package {raw['name']} is listed twice")
        names.add(raw["name"])
        if not SHA256.match(raw["sha256"]):
            raise bad(f"{raw['name']}: sha256 must be 64 lowercase hex digits")
        if not FILE.match(raw["file"]):
            raise bad(f"{raw['name']}: file must be a .conda file name")
        if raw["subdir"] not in (data["subdir"], "noarch"):
            raise bad(f"{raw['name']}: subdir {raw['subdir']!r} is neither "
                      f"{data['subdir']!r} nor 'noarch'")
        expected_url = f"{channel}/{raw['subdir']}/{raw['file']}"
        if raw["url"] != expected_url:
            raise bad(f"{raw['name']}: url must be {expected_url}")
        packages.append(LockedPackage(**raw))

    if data["tool"] not in names:
        raise bad(f"the tool package {data['tool']!r} is not in the lock")
    tool = next(p for p in packages if p.name == data["tool"])
    if tool.version != data["version"]:
        raise bad(f"the tool package is version {tool.version}, the lock "
                  f"says {data['version']}")
    return Lock(data["tool"], data["version"], data["subdir"], channel,
                packages)


def load_lock(path: Path) -> Lock:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ManagerError("lock_invalid", path=str(path), reason=str(exc))
    return parse_lock(data, str(path))


# ── Verification ────────────────────────────────────────────────────────────

def verify_file(path: Path, package: LockedPackage) -> None:
    """Refuse a downloaded file unless its size and SHA-256 match the lock.
    Nothing is unpacked before this passes."""
    size = path.stat().st_size
    if size != package.size:
        raise ManagerError("size_mismatch", path=str(path), found=size,
                           expected=package.size)
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK), b""):
            digest.update(chunk)
    if digest.hexdigest() != package.sha256:
        raise ManagerError("checksum_mismatch", path=str(path),
                           found=digest.hexdigest(), expected=package.sha256)


# ── Reading .conda packages ─────────────────────────────────────────────────

def _zstd():
    try:
        from compression import zstd  # Python 3.14 and later
    except ImportError:
        found = ".".join(str(n) for n in sys.version_info[:3])
        raise ManagerError("python_too_old", found=found)
    return zstd


def _inner(archive: zipfile.ZipFile, kind: str, where: str) -> str:
    names = [n for n in archive.namelist()
             if n.startswith(f"{kind}-") and n.endswith(".tar.zst")]
    if len(names) != 1:
        raise ManagerError("conda_invalid", path=where,
                           reason=f"expected one {kind}-*.tar.zst, "
                                  f"found {len(names)}")
    return names[0]


def _open_tar(archive: zipfile.ZipFile, name: str) -> tarfile.TarFile:
    zstd = _zstd()
    with archive.open(name) as raw:
        data = zstd.decompress(raw.read())
    return tarfile.open(fileobj=io.BytesIO(data), mode="r:")


def read_info(path: Path) -> Dict[str, object]:
    """``info/index.json`` and ``info/paths.json`` from a ``.conda`` file,
    which relocation follows."""
    where = str(path)
    try:
        with zipfile.ZipFile(path) as archive:
            info = _inner(archive, "info", where)
            _inner(archive, "pkg", where)
            with _open_tar(archive, info) as tar:
                wanted = {}
                for name in ("info/index.json", "info/paths.json"):
                    try:
                        member = tar.extractfile(name)
                    except KeyError:
                        member = None
                    if member is None:
                        raise ManagerError("conda_invalid", path=where,
                                           reason=f"{name} is missing")
                    wanted[name] = json.loads(member.read().decode("utf-8"))
    except (zipfile.BadZipFile, tarfile.TarError, ValueError) as exc:
        raise ManagerError("conda_invalid", path=where, reason=str(exc))
    paths = wanted["info/paths.json"]
    if not isinstance(paths, dict) or paths.get("paths_version") != 1:
        raise ManagerError("conda_invalid", path=where,
                           reason="info/paths.json is not paths_version 1")
    return {"index": wanted["info/index.json"], "paths": paths["paths"]}


def placeholders(info: Dict[str, object]) -> List[dict]:
    """The files that carry a build-prefix placeholder, with its mode."""
    return [entry for entry in info["paths"]
            if entry.get("prefix_placeholder")]


# ── Not yet implemented ─────────────────────────────────────────────────────

def unpack(path: Path, prefix: Path) -> None:
    """Unpack a verified package into a prefix, refusing absolute paths,
    ``..`` and links that leave the prefix."""
    raise ManagerError("not_implemented", command="install")


def relocate(info: Dict[str, object], prefix: Path) -> None:
    """Rewrite text placeholders by substitution and binary placeholders by
    substitution padded with null bytes, refusing a placeholder shorter
    than the prefix (decision 0001)."""
    raise ManagerError("not_implemented", command="install")
