"""Tests for tools/check_fidelity.py. Run: python -m unittest discover -s tests"""

import io
import json
import os
import shutil
import subprocess
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


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def write_config(d, cfg):
    path = os.path.join(d, "tali.fidelity.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f)
    return path


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

    def make(self, source, voice, cfg_extra=None, skeleton=None):
        d = tempfile.mkdtemp()
        write(os.path.join(d, "src", "doc.md"), source)
        write(os.path.join(d, "v", "doc.md"), voice)
        cfg = {"sources_root": "src", "voices": {"v": "v"}, **(cfg_extra or {})}
        if skeleton is not None:
            write(os.path.join(d, "skel", "doc.skeleton.md"), skeleton)
            cfg["skeletons_dir"] = "skel"
        return write_config(d, cfg)

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

    def test_object_voice_without_ref_is_a_working_tree_directory(self):
        path = self.make("Wait 3 days.", "Wait 3 days.", {"voices": {"v": {"dir": "v"}}})
        self.assertEqual(self.missing(path), [])

    def test_malformed_voice_entries_are_config_errors(self):
        for bad in ({"nope": "v"}, {"dir": "v", "refs": "x"}, 5, {}):
            path = self.make("Hi.", "Hi.", {"voices": {"v": bad}})
            with self.assertRaises(cf.ConfigError, msg=repr(bad)):
                cf.load_config(path)

    # fact skeletons

    SKELETON = (
        "# Fact skeleton: doc.md\n\n"
        "## Claims\n- C1: Uploads depend on the sync service.\n\n"
        "## Verbatim\n- V1: `npm ci`\n\n"
        "## Qualifiers\n- Q1: only when the sync service is running\n\n"
        "## Distinctions\n- D1: the CLI reads the config file; the desktop app does not\n"
    )

    def test_skeleton_qualifier_missing_from_voice_fails(self):
        path = self.make(
            "Run `npm ci`. Uploads work only when the sync service is running.",
            "Run `npm ci`. Uploads work.",
            skeleton=self.SKELETON,
        )
        self.assertEqual(self.missing(path), [
            {"kind": "skeleton qualifier", "item": "only when the sync service is running"},
        ])

    def test_skeleton_claims_and_distinctions_are_ignored(self):
        # Neither C1 nor D1 occurs in the source or the voice: no config
        # error about the source, no break against the voice.
        path = self.make(
            "Run `npm ci`. Uploads work only when the sync service is running.",
            "Run `npm ci`. Uploads work only when the sync service is running.",
            skeleton=self.SKELETON,
        )
        r = cf.check(cf.load_config(path))[0]
        self.assertEqual(r["missing"], [])
        self.assertEqual(r["checked"], 2)  # inline code + skeleton qualifier

    def test_skeleton_item_duplicating_an_auto_item_is_reported_once(self):
        path = self.make("Run `npm ci` now.", "Run it now.", skeleton="## Verbatim\n- V1: `npm ci`\n")
        self.assertEqual(self.missing(path), [{"kind": "inline code", "item": "npm ci"}])

    def test_skeleton_verbatim_inside_a_code_fence(self):
        fence = "```\ntali-agent --port 8080\n```\n"
        path = self.make(fence, fence, skeleton="## VERBATIM\n- V1: --port 8080\n")
        r = cf.check(cf.load_config(path))[0]
        self.assertEqual(r["missing"], [])
        self.assertEqual(r["checked"], 2)  # code block + skeleton verbatim

    def test_skeleton_phrase_absent_from_source_is_a_config_error(self):
        path = self.make("Hello.", "Hello.", skeleton="## Labels\n- L1: Sev-9\n")
        code, _, err = run_cli("--config", path)
        self.assertEqual(code, 2)
        self.assertIn("skeleton phrase not found in source doc.md: 'Sev-9'", err)

    def test_skeleton_bullet_without_id_is_a_config_error(self):
        path = self.make("Hello.", "Hello.", skeleton="## Qualifiers\n- Hello\n")
        with self.assertRaises(cf.ConfigError):
            cf.check(cf.load_config(path))

    def test_missing_skeleton_file_is_fine(self):
        path = self.make("Wait 3 days.", "Wait 3 days.", {"skeletons_dir": "skel"})
        self.assertEqual(self.missing(path), [])


SOURCE_README = (
    "# Team tools\n\n"
    "Every incident gets one of four severities: **Sev-1**, Sev-2, Sev-3, or Sev-4.\n"
    "Only public or fully synthetic data goes into the hosted service.\n"
    "Reviews take 3 days on average.\n"
)
SOURCE_SETUP = (
    "# Setup\n\nRun `npm ci`, then:\n\n```\ntali-agent --port 8080\n```\n\n"
    "Uploads work only when the sync service is running.\n"
)
FAITHFUL_README = (
    "# Team tools\n\n"
    "Each incident is labeled **Sev-1**, Sev-2, Sev-3, or Sev-4, and nothing else.\n"
    "The hosted service only ever gets public or fully synthetic data, and a\n"
    "review usually takes 3 days.\n"
)
FAITHFUL_SETUP = (
    "# Getting set up\n\nRun `npm ci` from the repo root, then:\n\n```\ntali-agent --port 8080\n```\n\n"
    "Uploads work only when the sync service is running.\n"
)
BROKEN_README = (
    "# Team tools\n\n"
    "Incidents get Sev-1, Sev-2 or Sev-3. Only public-ish data goes into the\n"
    "hosted service. Reviews take 3 days on average.\n"
)
FIDELITY = {
    "all": ["Sev-1", "Sev-2", "Sev-3", "Sev-4", "public or fully synthetic data"],
    "documents": {"guides/setup.md": ["only when the sync service is running"]},
}


@unittest.skipUnless(shutil.which("git"), "git is not on PATH")
class GitRefs(unittest.TestCase):
    """Sources pinned to a commit and voices kept on branches."""

    @classmethod
    def git(cls, *args):
        return subprocess.run(
            ["git", "-c", "user.email=t@t", "-c", "user.name=t",
             "-c", "commit.gpgsign=false", "-c", "core.autocrlf=false", *args],
            cwd=cls.repo, check=True, capture_output=True, text=True, encoding="utf-8",
        ).stdout

    @classmethod
    def setUpClass(cls):
        cls.repo = tempfile.mkdtemp()
        try:
            cls.git("init", "-q", "-b", "main")
        except subprocess.CalledProcessError:
            cls.git("init", "-q")
            cls.git("checkout", "-q", "-b", "main")

        docs = os.path.join(cls.repo, "docs")
        write(os.path.join(docs, "README.md"), SOURCE_README)
        write(os.path.join(docs, "guides", "setup.md"), SOURCE_SETUP)
        write(os.path.join(cls.repo, "voices", "plain", "README.md"), FAITHFUL_README)
        write(os.path.join(cls.repo, "voices", "plain", "guides", "setup.md"), FAITHFUL_SETUP)
        cls.git("add", "-A")
        cls.git("commit", "-q", "-m", "sources")
        cls.main_sha = cls.git("rev-parse", "HEAD").strip()

        cls.git("checkout", "-q", "-b", "voice-casual")
        write(os.path.join(docs, "README.md"), FAITHFUL_README)
        write(os.path.join(docs, "guides", "setup.md"), FAITHFUL_SETUP)
        cls.git("commit", "-q", "-a", "-m", "casual voice")

        cls.git("checkout", "-q", "main")
        cls.git("checkout", "-q", "-b", "voice-broken")
        write(os.path.join(docs, "README.md"), BROKEN_README)
        cls.git("rm", "-q", "docs/guides/setup.md")
        cls.git("commit", "-q", "-a", "-m", "broken voice")

        cls.git("checkout", "-q", "main")
        # Dirty the working tree so a check that read the checkout instead of
        # the pinned commit would see an empty source and prove nothing.
        write(os.path.join(docs, "README.md"), "# scratch\n")

        cls.config = write_config(cls.repo, {
            "sources_root": "docs",
            "sources_ref": cls.main_sha,
            "voices": {
                "casual": {"ref": "voice-casual"},
                "casual_explicit": {"ref": "voice-casual", "dir": "docs"},
                "broken": {"ref": "voice-broken"},
                "tree": "voices/plain",
            },
            "fidelity": FIDELITY,
        })
        cls.results = by_key(cf.check(cf.load_config(cls.config)))

    def test_branch_voice_passes(self):
        for voice in ("casual", "casual_explicit"):
            for doc in ("README.md", "guides/setup.md"):
                r = self.results[(voice, doc)]
                self.assertEqual(r["missing"], [], (voice, doc))
                self.assertGreater(r["checked"], 0)

    def test_working_tree_voice_checks_against_the_pinned_sources(self):
        for doc in ("README.md", "guides/setup.md"):
            r = self.results[("tree", doc)]
            self.assertEqual(r["missing"], [], doc)
            self.assertGreater(r["checked"], 0)

    def test_broken_branch_reports_breaks(self):
        missing = {(m["kind"], m["item"]) for m in self.results[("broken", "README.md")]["missing"]}
        self.assertEqual(missing, {
            ("fidelity phrase", "Sev-4"),
            ("fidelity phrase", "public or fully synthetic data"),
        })

    def test_document_missing_on_branch_is_a_missing_voice_copy(self):
        self.assertEqual(self.results[("broken", "guides/setup.md")]["missing"], [
            {"kind": "document", "item": "voice copy does not exist"},
        ])

    def test_cli_single_branch_voice(self):
        code, out, _ = run_cli("--config", self.config, "--voice", "casual")
        self.assertEqual(code, 0)
        self.assertIn("PASS: 2/2", out)
        self.assertEqual(run_cli("--config", self.config)[0], 1)

    def test_bad_voice_ref_exits_2_and_names_the_ref(self):
        path = write_config(tempfile.mkdtemp(dir=self.repo), {
            "sources_root": "../docs",
            "sources_ref": self.main_sha,
            "voices": {"x": {"ref": "voice-nope"}},
        })
        code, _, err = run_cli("--config", path)
        self.assertEqual(code, 2)
        self.assertIn("voice-nope", err)

    def test_bad_sources_ref_exits_2_and_names_the_ref(self):
        path = write_config(tempfile.mkdtemp(dir=self.repo), {
            "sources_root": "../docs",
            "sources_ref": "no-such-ref",
            "voices": {"x": "../voices/plain"},
        })
        code, _, err = run_cli("--config", path)
        self.assertEqual(code, 2)
        self.assertIn("no-such-ref", err)

    def test_sources_dir_missing_at_ref_exits_2(self):
        path = write_config(tempfile.mkdtemp(dir=self.repo), {
            "sources_root": "../nowhere",
            "sources_ref": self.main_sha,
            "voices": {"x": "../voices/plain"},
        })
        code, _, err = run_cli("--config", path)
        self.assertEqual(code, 2)
        self.assertIn("no .md documents under sources_root at ref", err)

    def test_ref_voice_outside_a_repository_exits_2(self):
        d = tempfile.mkdtemp()
        probe = subprocess.run(["git", "-C", d, "rev-parse", "--show-toplevel"], capture_output=True)
        if probe.returncode == 0:
            self.skipTest("temp directory is inside a git repository")
        write(os.path.join(d, "docs", "doc.md"), "Hi.")
        path = write_config(d, {"sources_root": "docs", "voices": {"x": {"ref": "main"}}})
        code, _, err = run_cli("--config", path)
        self.assertEqual(code, 2)
        self.assertIn("not a git repository", err)


if __name__ == "__main__":
    unittest.main()
