import os
import stat
import tempfile
import textwrap
import unittest
from pathlib import Path

import support  # noqa: F401
from osat_manager_git.baseline import check, parse_version, version_tuple

MANIFEST = {"baseline": {"version": 1, "minimum_version": "2.49.0"}}


def fake_git(directory: Path, version: str, config: dict) -> Path:
    """A stand-in git, as a POSIX shell script, answering --version and
    config --get from fixed values."""
    lines = ["#!/bin/sh",
             f'if [ "$1" = "--version" ]; then echo "git version {version}"; exit 0; fi',
             'if [ "$1" = "config" ] && [ "$2" = "--get" ]; then',
             '  case "$3" in']
    for key, value in config.items():
        lines.append(f'    {key}) echo "{value}"; exit 0 ;;')
    lines += ["  esac", "  exit 1", "fi", "exit 2"]
    path = directory / f"git-{version}"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return path


class VersionTests(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(parse_version("git version 2.56.0\n"), (2, 56, 0))
        self.assertEqual(parse_version("git version 2.56.0.windows.1"),
                         (2, 56, 0))
        self.assertIsNone(parse_version("not git"))

    def test_baseline_version(self):
        self.assertEqual(version_tuple("2.49.0"), (2, 49, 0))
        with self.assertRaises(ValueError):
            version_tuple("2.49")


@unittest.skipIf(os.name == "nt", "the stand-in git is a shell script")
class CheckTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_ready(self):
        git = fake_git(self.dir, "2.56.0", {"core.autocrlf": "false"})
        report = check(MANIFEST, {"core.autocrlf": "false"},
                       path_git=str(git))
        self.assertTrue(report.ready)
        self.assertEqual(report.installations[0].version, "2.56.0")

    def test_problems(self):
        old = fake_git(self.dir, "2.39.5", {"core.autocrlf": "true"})
        report = check(MANIFEST, {"core.autocrlf": "false",
                                  "core.longpaths": "true"},
                       path_git=str(old))
        self.assertFalse(report.ready)
        keys = [p.key for p in report.installations[0].problems]
        self.assertEqual(keys, ["problem_version_too_old",
                                "problem_config_wrong",
                                "problem_config_missing"])

    def test_unset_key_takes_git_default(self):
        git = fake_git(self.dir, "2.56.0", {})
        manifest = {"baseline": dict(MANIFEST["baseline"],
                                     unset_means={"core.autocrlf": "false"})}
        report = check(manifest, {"core.autocrlf": "false"},
                       path_git=str(git))
        self.assertTrue(report.ready)
        report = check(manifest, {"core.autocrlf": "true"},
                       path_git=str(git))
        self.assertEqual(report.installations[0].problems[0].key,
                         "problem_config_wrong")

    def test_unreadable(self):
        report = check(MANIFEST, {}, path_git=str(self.dir / "missing-git"))
        self.assertFalse(report.ready)
        self.assertEqual(report.installations[0].problems[0].key,
                         "problem_version_unreadable")

    def test_managed_and_json(self):
        first = fake_git(self.dir, "2.56.0", {})
        managed = fake_git(self.dir, "2.55.0", {})
        report = check(MANIFEST, {}, managed=[managed, first],
                       path_git=str(first))
        self.assertEqual([i.origin for i in report.installations],
                         ["path", "managed"])
        data = report.as_dict(lambda key, **f: key)
        self.assertTrue(data["ready"])
        self.assertEqual(data["installations"][1]["version"], "2.55.0")

    def test_no_git(self):
        report = check(MANIFEST, {}, search_path=False)
        self.assertFalse(report.ready)
        self.assertEqual(report.installations, [])


if __name__ == "__main__":
    unittest.main()
