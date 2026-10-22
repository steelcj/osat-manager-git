"""The manage-git command.

    manage-git --check [--json]        Check git against the baseline contract
    manage-git --install [VERSION]     Install a version, verified, and make it active
    manage-git --switch VERSION        Make an installed version active
    manage-git --status                Show the active, installed and archived versions and aliases
    manage-git --remove VERSION        Remove an installed version; its verified archive is kept
    manage-git --alias OLD=NEW         Rename an alias
    manage-git --self-install          Install the manager itself, so it works from any directory
    manage-git --uninstall [--yes]     Remove everything the manager owns
    manage-git --version               Show this manager's version

Every option except --check and --version is a skeleton at 0.1.0 and
says so; see ROADMAP.md.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import List, Optional

from . import __version__
from .baseline import check
from .errors import ManagerError
from .manifest import load_manifest
from .messages import Messages, choose_language
from .platforms import baseline_config, current_system, resolve_paths

NOT_YET = ("install", "switch", "status", "remove", "alias", "self_install",
           "uninstall")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="manage-git",
        description="Manage user-space installations of git from conda-forge, "
                    "and check git against the OSAT baseline.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true",
                       help="Check git against the baseline contract.")
    group.add_argument("--install", nargs="?", const="", metavar="VERSION",
                       help="Install a version and make it active "
                            "(default: the latest locked version).")
    group.add_argument("--switch", metavar="VERSION",
                       help="Make an installed version active.")
    group.add_argument("--status", action="store_true",
                       help="Show versions and aliases.")
    group.add_argument("--remove", metavar="VERSION",
                       help="Remove an installed version; its archive is kept.")
    group.add_argument("--alias", metavar="OLD=NEW", help="Rename an alias.")
    group.add_argument("--self-install", action="store_true",
                       help="Install the manager itself.")
    group.add_argument("--uninstall", action="store_true",
                       help="Remove everything the manager owns.")
    group.add_argument("--version", action="version",
                       version=f"manage-git {__version__}")
    parser.add_argument("--json", action="store_true",
                        help="--check: print the report as JSON.")
    parser.add_argument("--yes", action="store_true",
                        help="--uninstall: do not ask for confirmation.")
    parser.add_argument("--lang", metavar="TAG",
                        help="Language for messages: en-ca or fr-ca.")
    return parser


def root_guard() -> None:
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        raise ManagerError("run_as_user")


def run_check(manifest: dict, system: str, say: Messages,
              as_json: bool) -> int:
    paths = resolve_paths(manifest, system)
    managed = []
    if paths.versions.is_dir():
        managed = [paths.git(v.name) for v in sorted(paths.versions.iterdir())
                   if paths.git(v.name).is_file()]
    report = check(manifest, baseline_config(manifest, system), managed)
    if as_json:
        print(json.dumps(report.as_dict(say), indent=2, ensure_ascii=False))
        return 0 if report.ready else 2
    print(say("check_title", baseline=report.baseline,
              minimum=report.minimum_version))
    if not report.installations:
        print(say("check_no_git"))
        return 2
    for item in report.installations:
        print(say("installation_line", path=item.path,
                  origin=say(f"origin_{item.origin}"),
                  version=item.version or "?"))
        if item.meets:
            print(f"  {say('meets_baseline')}")
        for problem in item.problems:
            print(f"  {say(problem.key, **problem.fields)}")
    print(say("check_ready" if report.ready else "check_not_ready"))
    return 0 if report.ready else 2


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    say = Messages(choose_language(args.lang))
    try:
        root_guard()
        manifest = load_manifest()
        system = current_system()
        if args.check:
            return run_check(manifest, system, say, args.json)
        for command in NOT_YET:
            value = getattr(args, command)
            if value is not None and value is not False:
                raise ManagerError("not_implemented",
                                   command=command.replace("_", "-"))
        return 0
    except ManagerError as exc:
        message = say(exc.key, **exc.fields)
        print(say("error_prefix", message=message), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
