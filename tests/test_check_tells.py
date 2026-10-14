"""Tests for tools/check_tells.py. Run: python -m unittest discover -s tests"""

import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tools"))

import check_tells as ct  # noqa: E402

FIX = os.path.join(HERE, "fixtures", "tells")
CLEAN, EARNED, TELLY, CODE = (os.path.join(FIX, n + ".md") for n in ("clean", "earned", "telly", "code"))
ALL_RULES = {"vocabulary", "hedging-stack", "em-dash-density",
             "negation-contrast", "rhetorical-question", "symmetrical-ending"}


def run_cli(*args):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        try:
            code = ct.main(list(args))
        except SystemExit as e:
            code = e.code
    return code, out.getvalue(), err.getvalue()


def findings(*args):
    code, out, _ = run_cli(*args, "--json")
    data = json.loads(out)
    return code, data["pass"], data["findings"]


def line_of(path, needle):
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            if needle in line:
                return i
    raise AssertionError(f"{needle!r} not in {path}")


class Fixtures(unittest.TestCase):
    def test_clean_prose_passes_even_strict(self):
        for args in ((CLEAN,), (CLEAN, "--strict")):
            code, passed, found = findings(*args)
            self.assertEqual((code, passed, found), (0, True, []), args)
        self.assertIn("PASS: 0 strip, 0 review", run_cli(CLEAN)[1])

    def test_earned_negation_is_review_only(self):
        code, passed, found = findings(EARNED)
        self.assertEqual(code, 0)
        self.assertTrue(passed)
        self.assertEqual([(f["severity"], f["rule"]) for f in found],
                         [("review", "negation-contrast")])
        code, passed, _ = findings(EARNED, "--strict")
        self.assertEqual((code, passed), (1, False))

    def test_telly_triggers_every_rule(self):
        code, passed, found = findings(TELLY)
        self.assertEqual((code, passed), (1, False))
        self.assertEqual({f["rule"] for f in found}, ALL_RULES)
        severities = {f["rule"]: f["severity"] for f in found}
        self.assertEqual(severities, {
            "vocabulary": "strip", "hedging-stack": "strip", "em-dash-density": "strip",
            "negation-contrast": "review", "rhetorical-question": "review",
            "symmetrical-ending": "review",
        })
        self.assertIn("FAIL: ", run_cli(TELLY)[1])

    def test_every_vocabulary_group_fires(self):
        _, _, found = findings(TELLY)
        hits = {f["detail"].strip('"').lower() for f in found if f["rule"] == "vocabulary"}
        for key, forms in ct.VOCABULARY:
            self.assertTrue(hits & set(forms), f"no hit for {key}")

    def test_line_numbers_match_the_source_file(self):
        _, _, found = findings(TELLY)
        by_rule = {}
        for f in found:
            by_rule.setdefault(f["rule"], []).append(f)
        self.assertEqual(by_rule["hedging-stack"][0]["line"], line_of(TELLY, "This may potentially"))
        robust = [f for f in by_rule["vocabulary"] if f["detail"] == '"robust"']
        self.assertEqual([f["line"] for f in robust], [line_of(TELLY, "pipeline is robust")])
        self.assertEqual(by_rule["symmetrical-ending"][0]["line"], line_of(TELLY, "Read them"))

    def test_frontmatter_link_targets_and_code_are_skipped(self):
        _, _, found = findings(TELLY)
        frontmatter_end = line_of(TELLY, "description:") + 1
        self.assertFalse([f for f in found if f["line"] <= frontmatter_end])
        # "robust" and "leverage" in a link target, "seamless" in inline code: one body hit each
        self.assertEqual(sum(1 for f in found if f["detail"] == '"seamless"'), 1)
        code, passed, found = findings(CODE, "--strict")
        self.assertEqual((code, passed, found), (0, True, []))

    def test_allow_suppresses_a_vocabulary_group(self):
        code, _, found = findings(TELLY, "--allow", "robust", "--allow", "Leverages")
        details = [f["detail"].lower() for f in found if f["rule"] == "vocabulary"]
        self.assertFalse([d for d in details if "robust" in d or "leverag" in d])
        self.assertIn('"holistic"', details)
        self.assertEqual(code, 1)

    def test_json_shape(self):
        code, out, _ = run_cli(TELLY, "--json")
        data = json.loads(out)
        self.assertEqual(set(data), {"pass", "findings"})
        for f in data["findings"]:
            self.assertEqual(set(f), {"path", "line", "severity", "rule", "detail"})
            self.assertIn(f["severity"], ("strip", "review"))
        self.assertTrue(data["findings"][0]["path"].endswith("tells/telly.md"))

    def test_directory_is_recursed(self):
        code, _, found = findings(FIX)
        self.assertEqual(code, 1)
        self.assertEqual({os.path.basename(f["path"]) for f in found}, {"earned.md", "telly.md"})


class EmDashDensity(unittest.TestCase):
    def write(self, text):
        path = os.path.join(tempfile.mkdtemp(), "doc.md")
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        return path

    def dashes(self, *args):
        _, _, found = findings(*args)
        return [f for f in found if f["rule"] == "em-dash-density"]

    def test_fires_only_above_the_per_page_allowance(self):
        words = " ".join(["word"] * 60)
        self.assertEqual(self.dashes(self.write(f"# T\n\n{words} — more.\n")), [])
        two = self.write(f"# T\n\n{words} — more — and more.\n")
        self.assertEqual(len(self.dashes(two)), 1)
        self.assertIn("2 em dashes, allowance 1", self.dashes(two)[0]["detail"])
        self.assertEqual(self.dashes(two, "--page-words", "10"), [])

    def test_ascii_double_dash_counts_only_as_prose_dash(self):
        path = self.write("# T\n\nrun--then stop -- then go, with --strict unflagged.\n\n---\n")
        self.assertIn("2 em dashes", self.dashes(path)[0]["detail"])


class ExitCodes(unittest.TestCase):
    def test_missing_path_exits_2(self):
        code, _, err = run_cli(os.path.join(tempfile.mkdtemp(), "nope.md"))
        self.assertEqual(code, 2)
        self.assertIn("not a file or directory", err)

    def test_empty_directory_exits_2(self):
        self.assertEqual(run_cli(tempfile.mkdtemp())[0], 2)

    def test_bad_page_words_exits_2(self):
        self.assertEqual(run_cli(CLEAN, "--page-words", "0")[0], 2)


if __name__ == "__main__":
    unittest.main()
