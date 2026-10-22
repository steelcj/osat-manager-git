import contextlib
import io
import json
import os
import unittest
from unittest import mock

import support  # noqa: F401
from osat_manager_git import cli


def run(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err), \
            mock.patch.object(cli, "root_guard"):
        code = cli.main(list(argv))
    return code, out.getvalue(), err.getvalue()


class CliTests(unittest.TestCase):
    def test_not_implemented_is_said_plainly(self):
        code, _, err = run("--install", "--lang", "en-ca")
        self.assertEqual(code, 1)
        self.assertIn("--install is not implemented yet", err)
        code, _, err = run("--self-install", "--lang", "fr-ca")
        self.assertEqual(code, 1)
        self.assertIn("n'est pas encore implanté", err)

    @unittest.skipIf(os.name == "nt", "needs a POSIX environment")
    def test_check_json_shape(self):
        with mock.patch.dict(os.environ, {"OSAT_GIT_HOME": "/nonexistent"}):
            code, out, _ = run("--check", "--json")
        data = json.loads(out)
        self.assertIn(code, (0, 2))
        self.assertEqual(code == 0, data["ready"])
        for key in ("baseline", "minimum_version", "ready", "installations"):
            self.assertIn(key, data)


if __name__ == "__main__":
    unittest.main()
