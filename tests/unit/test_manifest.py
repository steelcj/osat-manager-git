import unittest

import support  # noqa: F401
from osat_manager_git.manifest import load_manifest, manifest_path
from osat_manager_git.platforms import baseline_config, conda_subdir
from osat_manager_git.baseline import version_tuple
from osat_manager_git.errors import ManagerError


class ManagerYamlTests(unittest.TestCase):
    def setUp(self):
        self.manifest = load_manifest()

    def test_found_in_checkout(self):
        self.assertEqual(manifest_path().name, "manager.yaml")

    def test_tool(self):
        tool = self.manifest["tool"]
        self.assertEqual(tool["name"], "git")
        self.assertEqual(tool["command"], "manage-git")
        self.assertEqual(tool["license"], "GPL-2.0-only")

    def test_conda_source(self):
        sources = self.manifest["sources"]
        self.assertEqual(sources["kind"], "conda")
        self.assertTrue(sources["channel"].startswith("https://"))
        self.assertIn("{version}", sources["lock"])
        self.assertIn("{subdir}", sources["lock"])

    def test_every_platform_complete(self):
        for system in ("linux", "macos", "windows"):
            platform = self.manifest["platforms"][system]
            self.assertTrue(platform["arch"], system)
            self.assertTrue(platform["executable"], system)
            self.assertIn(system, self.manifest["install_root"])
            self.assertIn(system, self.manifest["bin_dir"])

    def test_subdirs(self):
        self.assertEqual(conda_subdir(self.manifest, "linux", "x86_64"),
                         "linux-64")
        self.assertEqual(conda_subdir(self.manifest, "macos", "arm64"),
                         "osx-arm64")
        self.assertEqual(conda_subdir(self.manifest, "windows", "ARM64"),
                         "win-arm64")
        with self.assertRaises(ManagerError):
            conda_subdir(self.manifest, "linux", "riscv64")

    def test_windows_executable_is_cmd_git(self):
        self.assertEqual(self.manifest["platforms"]["windows"]["executable"],
                         "Library/cmd/git.exe")

    def test_baseline(self):
        version_tuple(self.manifest["baseline"]["minimum_version"])
        self.assertIn("core.longpaths",
                      baseline_config(self.manifest, "windows"))
        self.assertNotIn("core.longpaths",
                         baseline_config(self.manifest, "linux"))


if __name__ == "__main__":
    unittest.main()
