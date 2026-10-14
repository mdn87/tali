"""Tests for tools/check_fidelity.py. Run: python -m unittest discover -s tests"""

import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tools"))

import check_fidelity as cf  # noqa: E402

FIXTURE = os.path.join(HERE, "fixtures", "fidelity", "tali.fidelity.json")


def run_cli(*args):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = cf.main(list(args))
    return code, out.getvalue(), err.getvalue()


def by_key(results):
    return {(r["voice"], r["document"]): r for r in results}


class FixtureSet(unittest.TestCase):
    def setUp(self):
        self.results = by_key(cf.check(cf.load_config(FIXTURE)))

    def test_faithful_voice_passes(self):
        for doc in ("README.md", "guides/setup.md"):
            r = self.results[("plain", doc)]
            self.assertEqual(r["missing"], [], doc)
            self.assertGreater(r["checked"], 0)

    def test_broken_voice_reports_each_break(self):
        missing = {(m["kind"], m["item"]) for m in self.results[("broken", "README.md")]["missing"]}
        self.assertEqual(missing, {
            ("number", "3"),
            ("fidelity phrase", "Sev-3"),
            ("fidelity phrase", "Sev-4"),
            ("fidelity phrase", "public or fully synthetic data"),
        })

    def test_missing_voice_copy_fails(self):
        r = self.results[("broken", "guides/setup.md")]
        self.assertEqual(r["missing"][0]["kind"], "document")

    def test_cli_exit_codes(self):
        self.assertEqual(run_cli("--config", FIXTURE)[0], 1)
        code, out, _ = run_cli("--config", FIXTURE, "--voice", "plain")
        self.assertEqual(code, 0)
        self.assertIn("PASS: 2/2", out)

    def test_json_report(self):
        code, out, _ = run_cli("--config", FIXTURE, "--json")
        self.assertEqual(code, 1)
        self.assertFalse(json.loads(out)["pass"])


class Scratch(unittest.TestCase):
    """Small one-off document sets built in a temp directory."""

    def make(self, source, voice, cfg_extra=None):
        d = tempfile.mkdtemp()
        for sub, text in (("src", source), ("v", voice)):
            os.makedirs(os.path.join(d, sub))
            with open(os.path.join(d, sub, "doc.md"), "w", encoding="utf-8") as f:
                f.write(text)
        cfg = {"sources_root": "src", "voices": {"v": "v"}, **(cfg_extra or {})}
        path = os.path.join(d, "tali.fidelity.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(cfg, f)
        return path

    def missing(self, path):
        return cf.check(cf.load_config(path))[0]["missing"]

    def test_rewrapped_and_emphasised_phrase_still_matches(self):
        path = self.make(
            "It reduces exposure but is not a sandbox.",
            "It *reduces exposure*\nbut is **not** a sandbox.",
            {"fidelity": {"all": ["reduces exposure but is not a sandbox"]}},
        )
        self.assertEqual(self.missing(path), [])

    def test_changed_code_block_fails(self):
        path = self.make("```\nrun --fast\n```\n", "```\nrun --quick\n```\n")
        self.assertEqual(self.missing(path)[0]["kind"], "code block")

    def test_version_tokens_are_not_numbers(self):
        path = self.make("Sev-1 on v2 with mp3 files.", "Sev-1 on v2 with mp3 files.")
        self.assertEqual(cf.check(cf.load_config(path))[0]["checked"], 0)

    def test_number_is_not_matched_inside_a_larger_number(self):
        path = self.make("Wait 3 days.", "Wait 30 days.")
        self.assertEqual(self.missing(path), [{"kind": "number", "item": "3"}])

    def test_waiver_needs_reason_and_suppresses_break(self):
        waiver = {"item": "3", "reason": "owner approved 'three' spelled out"}
        path = self.make("Wait 3 days.", "Wait three days.", {"waivers": [waiver]})
        r = cf.check(cf.load_config(path))[0]
        self.assertEqual(r["missing"], [])
        self.assertEqual(r["waived"][0]["item"], "3")
        path = self.make("Wait 3 days.", "Wait three days.", {"waivers": [{"item": "3"}]})
        with self.assertRaises(cf.ConfigError):
            cf.check(cf.load_config(path))

    def test_stale_document_phrase_is_a_config_error(self):
        path = self.make("Hello.", "Hello.", {"fidelity": {"documents": {"doc.md": ["not in source"]}}})
        code, _, err = run_cli("--config", path)
        self.assertEqual(code, 2)
        self.assertIn("not found in source", err)

    def test_missing_config_exits_2(self):
        self.assertEqual(run_cli("--config", os.path.join(tempfile.mkdtemp(), "nope.json"))[0], 2)


if __name__ == "__main__":
    unittest.main()
