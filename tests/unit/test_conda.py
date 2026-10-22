import copy
import hashlib
import io
import json
import sys
import tarfile
import tempfile
import unittest
import zipfile
from pathlib import Path

import support  # noqa: F401
from osat_manager_git.conda import (load_lock, parse_lock, placeholders,
                                    read_info, verify_file)
from osat_manager_git.errors import ManagerError

CHANNEL = "https://conda.anaconda.org/conda-forge"
HAS_ZSTD = sys.version_info >= (3, 14)


def package(name="git", version="2.56.0", subdir="linux-64", data=b"x"):
    file = f"{name}-{version}-h0_0.conda"
    return {"name": name, "version": version, "build": "h0_0",
            "subdir": subdir, "file": file,
            "url": f"{CHANNEL}/{subdir}/{file}",
            "sha256": hashlib.sha256(data).hexdigest(), "size": len(data)}


def lock(*packages):
    return {"format": 1, "tool": "git", "version": "2.56.0",
            "subdir": "linux-64", "channel": CHANNEL,
            "packages": list(packages) or [package()]}


class LockTests(unittest.TestCase):
    def test_valid(self):
        parsed = parse_lock(lock(package(), package("ca-certificates",
                                                    "2026.7.22", "noarch")))
        self.assertEqual(parsed.subdir, "linux-64")
        self.assertEqual([p.name for p in parsed.packages],
                         ["git", "ca-certificates"])

    def assertRefused(self, data):
        with self.assertRaises(ManagerError) as caught:
            parse_lock(data)
        self.assertEqual(caught.exception.key, "lock_invalid")

    def test_refusals(self):
        cases = []
        extra = lock(); extra["note"] = "x"; cases.append(extra)
        wrong_format = lock(); wrong_format["format"] = 2; cases.append(wrong_format)
        http = lock(); http["channel"] = "http://example.org"; cases.append(http)
        empty = lock(); empty["packages"] = []; cases.append(empty)
        p = package(); p["url"] = "https://elsewhere.example/git.conda"
        cases.append(lock(p))
        p = package(); p["sha256"] = "ABC"; cases.append(lock(p))
        p = package(); p["size"] = 0; cases.append(lock(p))
        p = package(); p["size"] = True; cases.append(lock(p))
        p = package(subdir="win-64"); cases.append(lock(p))
        p = package(); p["file"] = "git.tar.bz2"; cases.append(lock(p))
        p = package(); p["signed"] = True; cases.append(lock(p))
        cases.append(lock(package(), package()))
        cases.append(lock(package("perl", "5.40.0")))
        cases.append(lock(package(version="2.55.0")))
        for data in cases:
            with self.subTest(data=data):
                self.assertRefused(data)

    def test_load_from_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "linux-64.json"
            path.write_text(json.dumps(lock()), encoding="utf-8")
            self.assertEqual(load_lock(path).version, "2.56.0")
            path.write_text("{not json", encoding="utf-8")
            with self.assertRaises(ManagerError):
                load_lock(path)


class VerifyTests(unittest.TestCase):
    def test_verify(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "git.conda"
            path.write_bytes(b"package bytes")
            good = parse_lock(lock(package(data=b"package bytes"))).packages[0]
            verify_file(path, good)
            wrong = parse_lock(lock(package(data=b"package bytez"))).packages[0]
            with self.assertRaises(ManagerError) as caught:
                verify_file(path, wrong)
            self.assertEqual(caught.exception.key, "checksum_mismatch")
            short = parse_lock(lock(package(data=b"short"))).packages[0]
            with self.assertRaises(ManagerError) as caught:
                verify_file(path, short)
            self.assertEqual(caught.exception.key, "size_mismatch")


def tar_zst(files):
    from compression import zstd
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as tar:
        for name, data in files.items():
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    return zstd.compress(buffer.getvalue())


def fake_conda(path, info_files, pkg_files=None, extra_info=False):
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("metadata.json", json.dumps({"conda_pkg_format_version": 2}))
        archive.writestr("pkg-git-2.56.0-h0_0.tar.zst",
                         tar_zst(pkg_files or {"bin/git": b"#!fake\n"}))
        archive.writestr("info-git-2.56.0-h0_0.tar.zst", tar_zst(info_files))
        if extra_info:
            archive.writestr("info-other-1.0-0.tar.zst", tar_zst(info_files))


@unittest.skipUnless(HAS_ZSTD, "compression.zstd needs Python 3.14")
class ReadInfoTests(unittest.TestCase):
    INDEX = json.dumps({"name": "git", "version": "2.56.0"}).encode()
    PATHS = json.dumps({"paths_version": 1, "paths": [
        {"_path": "bin/git", "path_type": "hardlink",
         "prefix_placeholder": "/opt/placeholder_" + "p" * 200,
         "file_mode": "binary"},
        {"_path": "share/doc/README", "path_type": "hardlink"}]}).encode()

    def test_reads_index_and_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "git.conda"
            fake_conda(path, {"info/index.json": self.INDEX,
                              "info/paths.json": self.PATHS})
            info = read_info(path)
            self.assertEqual(info["index"]["name"], "git")
            self.assertEqual([p["_path"] for p in placeholders(info)],
                             ["bin/git"])

    def test_refusals(self):
        with tempfile.TemporaryDirectory() as tmp:
            cases = {
                "no-paths": dict(info_files={"info/index.json": self.INDEX}),
                "paths-v2": dict(info_files={
                    "info/index.json": self.INDEX,
                    "info/paths.json": json.dumps({"paths_version": 2,
                                                   "paths": []}).encode()}),
                "two-info": dict(info_files={"info/index.json": self.INDEX,
                                             "info/paths.json": self.PATHS},
                                 extra_info=True),
            }
            for name, kwargs in cases.items():
                with self.subTest(name):
                    path = Path(tmp) / f"{name}.conda"
                    fake_conda(path, **kwargs)
                    with self.assertRaises(ManagerError) as caught:
                        read_info(path)
                    self.assertEqual(caught.exception.key, "conda_invalid")
            notzip = Path(tmp) / "not.conda"
            notzip.write_bytes(b"plain bytes")
            with self.assertRaises(ManagerError):
                read_info(notzip)


if __name__ == "__main__":
    unittest.main()
