"""The baseline contract: what "git is ready" means for other managers.

``check`` looks at the first git on ``PATH`` and every version the
manager has installed, and reports each against the baseline in
manager.yaml: a minimum version and required configuration values.
Checking runs only the git being checked, never a shell, and runs it from
a fresh empty directory so no repository's own configuration is read.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

VERSION = re.compile(r"\bgit version (\d+)\.(\d+)\.(\d+)")
TIMEOUT = 20


@dataclass
class Problem:
    key: str
    fields: Dict[str, str]


@dataclass
class Installation:
    path: str
    origin: str                       # "path" or "managed"
    version: Optional[str] = None
    problems: List[Problem] = field(default_factory=list)

    @property
    def meets(self) -> bool:
        return self.version is not None and not self.problems


@dataclass
class Report:
    baseline: int
    minimum_version: str
    installations: List[Installation]

    @property
    def ready(self) -> bool:
        first = next((i for i in self.installations if i.origin == "path"),
                     None)
        return first is not None and first.meets

    def as_dict(self, render=None) -> dict:
        def problem(p: Problem) -> dict:
            out = {"code": p.key, **p.fields}
            if render:
                out["message"] = render(p.key, **p.fields)
            return out
        return {
            "baseline": self.baseline,
            "minimum_version": self.minimum_version,
            "ready": self.ready,
            "installations": [
                {"path": i.path, "origin": i.origin, "version": i.version,
                 "meets": i.meets,
                 "problems": [problem(p) for p in i.problems]}
                for i in self.installations],
        }


def parse_version(text: str) -> Optional[Tuple[int, int, int]]:
    """``git version 2.56.0`` and ``git version 2.56.0.windows.1`` both
    read as (2, 56, 0)."""
    match = VERSION.search(text)
    return tuple(int(n) for n in match.groups()) if match else None


def version_tuple(text: str) -> Tuple[int, int, int]:
    parts = text.split(".")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        raise ValueError(f"not a three-part version: {text!r}")
    return tuple(int(p) for p in parts)


def _run(git: str, args: Sequence[str], cwd: str) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["GIT_CEILING_DIRECTORIES"] = cwd
    env.pop("GIT_DIR", None)
    env.pop("GIT_CONFIG", None)
    env["LC_ALL"] = "C"
    return subprocess.run([git, *args], cwd=cwd, env=env, capture_output=True,
                          text=True, timeout=TIMEOUT, check=False)


def inspect(git: str, origin: str, minimum: str,
            config: Dict[str, str],
            unset_means: Optional[Dict[str, str]] = None) -> Installation:
    unset_means = unset_means or {}
    found = Installation(path=git, origin=origin)
    with tempfile.TemporaryDirectory(prefix="manage-git-check-") as cwd:
        try:
            result = _run(git, ["--version"], cwd)
        except (OSError, subprocess.SubprocessError) as exc:
            found.problems.append(Problem("problem_version_unreadable",
                                          {"detail": str(exc)}))
            return found
        parsed = parse_version(result.stdout)
        if result.returncode != 0 or parsed is None:
            detail = (result.stderr or result.stdout).strip() or \
                f"exit status {result.returncode}"
            found.problems.append(Problem("problem_version_unreadable",
                                          {"detail": detail}))
            return found
        found.version = ".".join(str(n) for n in parsed)
        if parsed < version_tuple(minimum):
            found.problems.append(Problem("problem_version_too_old",
                                          {"found": found.version,
                                           "minimum": minimum}))
        for key, expected in config.items():
            value = _run(git, ["config", "--get", key], cwd)
            current = value.stdout.strip() if value.returncode == 0 else None
            if current is None:
                current = unset_means.get(key)
            if current is None:
                found.problems.append(Problem("problem_config_missing",
                                              {"key": key,
                                               "expected": expected}))
            elif current.lower() != expected.lower():
                found.problems.append(Problem("problem_config_wrong",
                                              {"key": key, "found": current,
                                               "expected": expected}))
    return found


def check(manifest: dict, config: Dict[str, str],
          managed: Sequence[Path] = (),
          path_git: Optional[str] = None,
          search_path: bool = True) -> Report:
    """Report the first git on PATH and each managed git against the
    baseline. ``path_git`` overrides the PATH lookup, for tests."""
    baseline = manifest["baseline"]
    minimum = baseline["minimum_version"]
    version_tuple(minimum)            # refuse a malformed baseline early
    installations = []
    first = path_git if path_git is not None else (
        shutil.which("git") if search_path else None)
    unset = dict(baseline.get("unset_means") or {})
    seen = set()
    if first:
        installations.append(inspect(first, "path", minimum, config, unset))
        seen.add(os.path.realpath(first))
    for git in managed:
        if os.path.realpath(git) in seen:
            continue
        installations.append(inspect(str(git), "managed", minimum, config,
                                     unset))
    return Report(int(baseline["version"]), minimum, installations)
