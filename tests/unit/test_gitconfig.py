import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import support  # noqa: F401
from osat_manager_git.baseline import check
from osat_manager_git.errors import ManagerError
from osat_manager_git.gitconfig import (ENV_VAR, Invocation,
                                        render_system_config, write_text)
from osat_manager_git.platforms import Paths, render_launcher

GIT = shutil.which("git")
MANIFEST = {"baseline": {"version": 1, "minimum_version": "2.0.0"}}


class RenderTests(unittest.TestCase):
    def test_include_comes_before_the_baseline(self):
        text = render_system_config(Path("/p/etc/gitconfig"),
                                    {"core.autocrlf": "false"})
        self.assertLess(text.index("[include]"), text.index("[core]"))
        self.assertIn('path = "/p/etc/gitconfig"', text)
        self.assertIn('autocrlf = "false"', text)

    def test_no_package_file_means_no_include(self):
        text = render_system_config(None, {"core.autocrlf": "false"})
        self.assertNotIn("[include]", text)

    def test_windows_paths_use_forward_slashes(self):
        text = render_system_config(
            Path("C:\\Users\\a b\\osat\\git\\versions\\2.56.0\\Library\\etc\\gitconfig"),
            {})
        self.assertIn('path = "C:/Users/a b/osat/git/versions/2.56.0/'
                      'Library/etc/gitconfig"', text)

    def test_sections_are_grouped_and_subsections_quoted(self):
        text = render_system_config(None, {"core.autocrlf": "false",
                                           "filter.lfs.required": "false",
                                           "core.longpaths": "true"})
        self.assertEqual(text.count("[core]"), 1)
        self.assertIn('[filter "lfs"]\n\trequired = "false"', text)

    def test_multi_valued_key_is_reset_first(self):
        text = render_system_config(None, {"credential.helper": "manager"})
        self.assertIn('[credential]\n\thelper =\n\thelper = "manager"', text)

    def test_values_are_escaped(self):
        text = render_system_config(None, {"core.editor": 'a "b" \\c'})
        self.assertIn('editor = "a \\"b\\" \\\\c"', text)

    def test_bad_keys_and_values_are_refused(self):
        for key in ("autocrlf", ".x", "core.", "co re.x"):
            with self.assertRaises(ManagerError):
                render_system_config(None, {key: "1"})
        with self.assertRaises(ManagerError):
            render_system_config(None, {"core.editor": "a\nb"})


class LauncherTests(unittest.TestCase):
    def test_posix_launcher(self):
        text = render_launcher(False, Invocation(
            "/home/a'b/git", {ENV_VAR: "/home/a/cfg"}))
        self.assertTrue(text.startswith("#!/bin/sh\n"))
        self.assertIn("GIT_CONFIG_SYSTEM='/home/a/cfg'\nexport GIT_CONFIG_SYSTEM",
                      text)
        self.assertIn("exec '/home/a'\\''b/git' \"$@\"", text)
        self.assertNotIn("PATH", text)

    def test_windows_launcher(self):
        text = render_launcher(True, Invocation(
            "C:\\U\\100%\\git.exe", {ENV_VAR: "C:\\U\\cfg"}))
        self.assertIn('set "GIT_CONFIG_SYSTEM=C:\\U\\cfg"\r\n', text)
        self.assertIn('"C:\\U\\100%%\\git.exe" %*\r\n', text)
        self.assertTrue(text.endswith("exit /b %ERRORLEVEL%\r\n"))
        with self.assertRaises(ManagerError):
            render_launcher(True, Invocation('C:\\a"b\\git.exe'))

    def test_paths_give_the_invocation(self):
        paths = Paths(Path("/r"), Path("/b"), "bin/git", False,
                      "etc/gitconfig")
        invocation = paths.invocation("2.56.0")
        self.assertEqual(invocation.executable, "/r/versions/2.56.0/bin/git")
        self.assertEqual(invocation.env,
                         {ENV_VAR: "/r/config/2.56.0/gitconfig"})
        self.assertEqual(paths.package_config("2.56.0"),
                         Path("/r/versions/2.56.0/etc/gitconfig"))
        self.assertIsNone(Paths(Path("/r"), Path("/b"), "bin/git", False)
                          .package_config("2.56.0"))


@unittest.skipUnless(GIT, "needs a git to read the rendered file")
class GitReadsItTests(unittest.TestCase):
    """The rendered file, read by a real git through GIT_CONFIG_SYSTEM."""

    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix="manage-git-test-"))
        self.addCleanup(shutil.rmtree, self.dir)
        self.package = self.dir / "package-gitconfig"
        self.package.write_text("[core]\n\tautocrlf = true\n"
                                "[credential]\n\thelper = helper-selector\n"
                                "[http]\n\tsslCAInfo = /prefix/ssl/cacert.pem\n",
                                encoding="utf-8")
        self.mine = self.dir / "config" / "2.56.0" / "gitconfig"
        write_text(self.mine, render_system_config(
            self.package, {"core.autocrlf": "false",
                           "credential.helper": "manager"}))

    def git(self, *args):
        env = {"PATH": os.environ.get("PATH", ""), "HOME": str(self.dir),
               "GIT_CONFIG_GLOBAL": os.devnull, ENV_VAR: str(self.mine),
               "GIT_CEILING_DIRECTORIES": str(self.dir)}
        return subprocess.run([GIT, *args], cwd=self.dir, env=env,
                              capture_output=True, text=True, check=True
                              ).stdout.strip()

    def test_baseline_wins_and_package_values_remain(self):
        self.assertEqual(self.git("config", "--get", "core.autocrlf"), "false")
        self.assertEqual(self.git("config", "--get", "http.sslCAInfo"),
                         "/prefix/ssl/cacert.pem")

    def test_multi_valued_reset_follows_the_package_value(self):
        # git lists every value; its credential code clears the list at
        # the empty one, so only the baseline's helper is used.
        helpers = self.git("config", "--get-all", "credential.helper")
        self.assertEqual(helpers.splitlines(),
                         ["helper-selector", "", "manager"])

    def test_check_uses_the_invocation(self):
        invocation = Invocation(GIT, {ENV_VAR: str(self.mine)})
        report = check(MANIFEST, {"core.autocrlf": "false"}, [invocation],
                       search_path=False)
        [found] = report.installations
        self.assertEqual(found.problems, [])
        self.assertEqual(report.as_dict()["installations"][0]["invocation"],
                         {"executable": GIT, "env": {ENV_VAR: str(self.mine)}})

    def test_missing_system_file_is_one_problem(self):
        invocation = Invocation(GIT, {ENV_VAR: str(self.dir / "gone")})
        report = check(MANIFEST, {}, [invocation], search_path=False)
        [found] = report.installations
        self.assertEqual([p.key for p in found.problems],
                         ["problem_system_config_missing"])


if __name__ == "__main__":
    unittest.main()
