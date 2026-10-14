"""The worked example under examples/handbook must check clean and build.

Run: python -m unittest discover -s tests
"""

import io
import os
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tools"))

import build_page  # noqa: E402
import build_site  # noqa: E402
import check_fidelity  # noqa: E402
import check_tells  # noqa: E402

EXAMPLE = os.path.abspath(os.path.join(HERE, "..", "examples", "handbook"))


def run(main, *argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = main(list(argv))
    return code, out.getvalue(), err.getvalue()


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


class Example(unittest.TestCase):
    def copy(self):
        tmp = tempfile.mkdtemp()
        shutil.copytree(EXAMPLE, tmp, dirs_exist_ok=True, ignore=shutil.ignore_patterns("site"))
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        return tmp

    def test_fidelity_check_passes(self):
        code, out, err = run(check_fidelity.main, "--config", os.path.join(EXAMPLE, "tali.fidelity.json"))
        self.assertEqual(code, 0, err)
        self.assertIn("PASS: 3/3", out)

    def test_plain_voice_has_no_strip_tells(self):
        code, out, _ = run(check_tells.main, os.path.join(EXAMPLE, "voices", "plain"))
        self.assertEqual(code, 0, out)
        self.assertIn("PASS: 0 strip", out)

    def test_committed_page_matches_sources(self):
        code, out, err = run(build_page.main, "--config", os.path.join(EXAMPLE, "tali.site.json"), "--check")
        self.assertEqual(code, 0, err)
        self.assertIn("(changed: 0)", out)

    def test_site_builds_both_voices(self):
        tmp = self.copy()
        code, out, err = run(build_site.main, "--config", os.path.join(tmp, "tali.site.json"))
        self.assertEqual(code, 0, err)
        index = read(os.path.join(tmp, "site", "index.html"))
        plain = read(os.path.join(tmp, "site", "plain.html"))
        # the overview section is the cover, so compare prose in the setup section
        self.assertIn("Expect it to take about 20 minutes", index)
        self.assertIn("Plan on about 20 minutes", plain)
        self.assertIn("the team responds within one business day", index)
        self.assertIn("plain-voice edition", plain)  # covers/overview-plain.md
        self.assertNotIn("plain-voice edition", index)
        self.assertIn("public or fully synthetic data", plain)

    def test_a_dropped_qualifier_fails_the_check(self):
        tmp = self.copy()
        path = os.path.join(tmp, "voices", "plain", "policy", "data-handling.md")
        text = read(path).replace("reduces exposure but is not a sandbox", "reduces exposure")
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        code, out, _ = run(check_fidelity.main, "--config", os.path.join(tmp, "tali.fidelity.json"))
        self.assertEqual(code, 1)
        self.assertIn("FAIL plain/policy/data-handling.md", out)
        self.assertIn("reduces exposure but is not a sandbox", out)


if __name__ == "__main__":
    unittest.main()
