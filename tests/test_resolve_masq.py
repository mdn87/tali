"""Tests for tools/resolve_masq_profile.py. Run: python -m unittest discover -s tests"""

import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tools"))

import resolve_masq_profile as rm  # noqa: E402


def run(*argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = rm.main(list(argv))
    return code, out.getvalue().strip(), err.getvalue()


class Resolve(unittest.TestCase):
    def setUp(self):
        self.plugins = tempfile.mkdtemp()
        self.install = os.path.join(self.plugins, "cache", "masq", "masq", "0.7.0")
        os.makedirs(os.path.join(self.install, "profiles"))
        with open(os.path.join(self.install, "profiles", "dean.md"), "w", encoding="utf-8") as f:
            f.write("# Dean\n")
        with open(os.path.join(self.plugins, "installed_plugins.json"), "w", encoding="utf-8") as f:
            json.dump({"version": 2, "plugins": {
                "other@x": [{"installPath": "/nowhere"}],
                "masq@masq": [{"installPath": self.install}],
            }}, f)
        os.environ.pop("MASQ_PLUGIN_ROOT", None)

    def test_resolves_from_installed_plugins(self):
        code, out, _ = run("dean", "--plugins-dir", self.plugins)
        self.assertEqual(code, 0)
        self.assertEqual(out, os.path.join(self.install, "profiles", "dean.md"))

    def test_explicit_root_wins(self):
        other = tempfile.mkdtemp()
        os.makedirs(os.path.join(other, "profiles"))
        open(os.path.join(other, "profiles", "dean.md"), "w").close()
        code, out, _ = run("dean", "--plugins-dir", self.plugins, "--root", other)
        self.assertEqual(code, 0)
        self.assertEqual(out, os.path.join(other, "profiles", "dean.md"))

    def test_marketplace_clone_fallback(self):
        clone = os.path.join(self.plugins, "marketplaces", "masq", "profiles")
        os.makedirs(clone)
        open(os.path.join(clone, "plain.md"), "w").close()
        code, out, _ = run("plain", "--plugins-dir", self.plugins)
        self.assertEqual(code, 0)
        self.assertTrue(out.endswith(os.path.join("masq", "profiles", "plain.md")))

    def test_not_found_lists_places_searched(self):
        code, out, err = run("ghost", "--plugins-dir", self.plugins)
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertIn("searched", err)
        self.assertIn(self.install, err)

    def test_rejects_paths_as_ids(self):
        self.assertEqual(run("../dean", "--plugins-dir", self.plugins)[0], 2)


if __name__ == "__main__":
    unittest.main()
