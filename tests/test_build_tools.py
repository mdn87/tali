"""Tests for the publish tools: build_page, build_site, build_pdf, init_site.

Run: python -m unittest discover -s tests
"""

import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "tools"))

import build_page  # noqa: E402
import build_pdf  # noqa: E402
import build_site  # noqa: E402
import init_site  # noqa: E402

FIXTURE = os.path.join(HERE, "fixtures", "site")
GIT = shutil.which("git")


def run(main, *argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = main(list(argv))
    return code, out.getvalue(), err.getvalue()


def git(cwd, *args):
    return subprocess.run(
        ["git", "-c", "user.email=t@t", "-c", "user.name=t", *args],
        cwd=cwd, capture_output=True, text=True, encoding="utf-8", check=True,
    ).stdout.strip()


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


class Converter(unittest.TestCase):
    def setUp(self):
        build_page.configure({
            "link_map": {"README.md": "#readme", "setup.md": "#guides-setup"},
            "chips": [{"label": "Recommended", "class": "ok"}],
            "skip_prefixes": ["**Status:**"],
            "section_sources": {"readme": "README.md", "guides-setup": "guides/setup.md"},
        })

    def conv(self, md):
        return build_page.convert(md, "readme")

    def test_nested_list_stays_nested(self):
        out = self.conv("- top\n  - inner\n- second\n")
        self.assertRegex(out, r"<li>top\s*<ul>\s*<li>inner</li>\s*</ul></li>")
        self.assertEqual(out.count("<ul>"), 2)

    def test_blank_lines_between_items_keep_one_list(self):
        out = self.conv("1. one\n\n2. two\n\n- a\n\n- b\n")
        self.assertEqual(out.count("<ol>"), 1)
        self.assertEqual(out.count("<ul>"), 1)
        self.assertEqual(out.count("<li>"), 4)

    def test_list_then_paragraph(self):
        out = self.conv("- a\n- b\n\nAfter.\n")
        self.assertIn("</ul>", out)
        self.assertIn("<p>After.</p>", out)

    def test_horizontal_rule(self):
        self.assertIn("<hr>", self.conv("Before.\n\n---\n\nAfter.\n"))
        self.assertNotIn("<p>---</p>", self.conv("---\n"))

    def test_deep_headings_and_ids(self):
        out = self.conv("## Big Thing\n\n##### Five\n\n###### Six\n\n## Big Thing\n")
        self.assertIn('<h2 id="readme--big-thing">Big Thing</h2>', out)
        self.assertIn('<h5 id="readme--five">Five</h5>', out)
        self.assertIn('<h6 id="readme--six">Six</h6>', out)
        self.assertIn('id="readme--big-thing-2"', out)

    def test_image(self):
        self.assertIn('<img src="pic.png" alt="A pic">', self.conv("See ![A pic](pic.png) here.\n"))

    def test_links(self):
        out = self.conv(
            "[a](guides/setup.md) [b](README.md#how-it-works) [c](#local-heading) "
            "[d](#guides-setup) [e](notes.md) [f](https://x.example/p?q=1)\n"
        )
        self.assertIn('<a href="#guides-setup">a</a>', out)
        self.assertIn('<a href="#readme--how-it-works">b</a>', out)
        self.assertIn('<a href="#readme--local-heading">c</a>', out)
        self.assertIn('<a href="#guides-setup">d</a>', out)
        self.assertIn(" e ", out)
        self.assertNotIn(">e</a>", out)
        self.assertIn('<a href="https://x.example/p?q=1">f</a>', out)

    def test_chip_table_quote_code_checklist(self):
        out = self.conv(
            "**Recommended.** Do it.\n\n| A | B |\n|---|---|\n| 1 | 2 |\n\n> q1\n> q2\n\n"
            "```equation\nx + y\n```\n\n- [ ] open\n- [x] done\n"
        )
        self.assertIn('<span class="chip ok">Recommended.</span> Do it.', out)
        self.assertIn("<th>A</th><th>B</th>", out)
        self.assertIn("<blockquote><p>q1 q2</p></blockquote>", out)
        self.assertIn('<pre class="equation">x + y</pre>', out)
        self.assertIn('<ul class="check">', out)
        self.assertIn("<li>open</li>", out)

    def test_title_and_skip_prefix_dropped(self):
        out = self.conv("# Title\n**Status:** draft\n\nBody.\n")
        self.assertEqual(out, "<p>Body.</p>")


class Scaffold(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        shutil.copytree(FIXTURE, self.tmp, dirs_exist_ok=True)
        code, out, err = run(
            init_site.main, "--sources", os.path.join(self.tmp, "docs"), "--out", self.tmp,
            "--title", "Probe Handbook", "--subtitle", "a probe", "--voices", "plain,casual",
        )
        self.assertEqual(code, 0, err)
        self.cfg = os.path.join(self.tmp, "tali.site.json")
        self.page = os.path.join(self.tmp, "handbook.html")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_scaffold_writes_filled_page_and_configs(self):
        page = read(self.page)
        for sid in ("readme", "guides-setup", "reference-glossary"):
            self.assertIn(f'<section class="doc" id="doc-{sid}" hidden>', page)
        self.assertIn('<div class="grp-label">Documents</div>', page)
        self.assertIn('<div class="grp-label">Guides</div>', page)
        self.assertIn('<a class="navlink" href="#guides-setup">Setup</a>', page)
        self.assertIn("<strong>Sev-1</strong>", page)  # filled, not placeholder
        self.assertIn("<title>Probe Handbook</title>", page)
        self.assertTrue(os.path.isfile(os.path.join(self.tmp, "tali.fidelity.json")))
        cfg = build_page.load_config(self.cfg)
        self.assertEqual(cfg["section_sources"]["guides-setup"], "guides/setup.md")
        self.assertEqual(cfg["link_map"]["glossary.md"], "#reference-glossary")
        self.assertEqual([v["key"] for v in cfg["versions"]], ["orig", "plain", "casual"])

    def test_refuses_to_overwrite_without_force(self):
        code, _, err = run(init_site.main, "--sources", os.path.join(self.tmp, "docs"), "--out", self.tmp)
        self.assertEqual(code, 2)
        self.assertIn("--force", err)
        code, _, _ = run(init_site.main, "--sources", os.path.join(self.tmp, "docs"), "--out", self.tmp, "--force")
        self.assertEqual(code, 0)

    def test_build_page_check_and_missing_source(self):
        code, out, _ = run(build_page.main, "--config", self.cfg, "--check")
        self.assertEqual(code, 0)
        self.assertIn("regenerated from markdown: 3", out)
        run(build_page.main, "--config", self.cfg)
        once = read(self.page)
        run(build_page.main, "--config", self.cfg)
        self.assertEqual(read(self.page), once)  # rebuilding is idempotent
        os.remove(os.path.join(self.tmp, "docs", "guides", "setup.md"))
        code, _, err = run(build_page.main, "--config", self.cfg, "--check")
        self.assertEqual(code, 2)
        self.assertIn("guides-setup", err)
        self.assertNotIn("Traceback", err)

    def test_site_skips_voice_dir_that_does_not_exist_yet(self):
        code, out, _ = run(build_site.main, "--config", self.cfg)
        self.assertEqual(code, 0)
        self.assertIn("skipping casual.html", out)
        self.assertTrue(os.path.isfile(os.path.join(self.tmp, "site", "plain.html")))

    @unittest.skipUnless(GIT, "git not available")
    def test_build_site_versions_from_tree_dir_and_refs(self):
        git(self.tmp, "init", "-q")
        git(self.tmp, "symbolic-ref", "HEAD", "refs/heads/main")
        git(self.tmp, "add", "-A")
        git(self.tmp, "commit", "-q", "-m", "init")
        pinned = git(self.tmp, "rev-parse", "HEAD")
        git(self.tmp, "checkout", "-q", "-b", "voice-casual")
        # mark the setup section: the readme section gets replaced by the casual cover
        page = read(self.page).replace("in the repo root, then start", "CASUALVOICE in the repo root, then start")
        open(self.page, "w", encoding="utf-8").write(page)
        git(self.tmp, "commit", "-q", "-am", "casual")
        git(self.tmp, "checkout", "-q", "main")

        cfg = build_page.load_config(self.cfg)
        cfg.pop("_dir")
        cfg["versions"] = [
            {"key": "orig", "file": "original.html", "url": "/original", "label": "Original",
             "subtitle_suffix": " · original", "ref": pinned},
            {"key": "plain", "file": "index.html", "url": "/", "label": "Plain",
             "subtitle_suffix": "", "sources_root": "voices/plain"},
            {"key": "casual", "file": "casual.html", "url": "/casual", "label": "Casual",
             "subtitle_suffix": " · casual", "ref": "voice-casual"},
            {"key": "gone", "file": "gone.html", "url": "/gone", "label": "Gone", "ref": "no-such-ref"},
        ]
        init_site.write_json(self.cfg, cfg)

        code, out, err = run(build_site.main, "--config", self.cfg)
        self.assertEqual(code, 0, err)
        site = os.path.join(self.tmp, "site")
        self.assertEqual(sorted(os.listdir(site)), ["casual.html", "index.html", "original.html"])
        self.assertIn("skipping gone.html", out)

        index, casual, original = (read(os.path.join(site, f)) for f in ("index.html", "casual.html", "original.html"))
        self.assertIn("PLAINVOICE", index)
        self.assertNotIn("PLAINVOICE", original)
        self.assertIn("CASUALVOICE", casual)
        self.assertNotIn("CASUALVOICE", original)
        self.assertIn("Casual cover", casual)  # covers/readme-casual.md
        self.assertNotIn("Casual cover", index)
        self.assertIn('class="tablewrap wide"', index)  # four-column glossary
        self.assertIn('class="vswitch"', index)
        self.assertIn('data-href="/casual"', index)
        self.assertIn("a probe · casual</div>", casual)
        self.assertIn('<meta charset="utf-8">', index[:1024])
        self.assertIn('name="robots"', index)

    def test_build_pdf_portable_wrapper_and_overrides(self):
        try:
            chrome = build_pdf.find_chrome()
        except build_page.ConfigError:
            self.skipTest("no headless browser on this machine")
        code, out, err = run(build_pdf.main, "--config", self.cfg)
        self.assertEqual(code, 0, err)
        pdf = os.path.join(self.tmp, "handbook.pdf")
        self.assertGreater(os.path.getsize(pdf), 1000)
        run(build_site.main, "--config", self.cfg)
        code, out, err = run(build_pdf.main, "--config", self.cfg, "--page", "site/plain.html",
                             "--pdf", "handbook-plain.pdf", "--label", "test", "--chrome", chrome)
        self.assertEqual(code, 0, err)
        self.assertGreater(os.path.getsize(os.path.join(self.tmp, "handbook-plain.pdf")), 1000)
        self.assertTrue(os.path.isfile(os.path.join(self.tmp, "site", "handbook-plain.pdf")))

    def test_print_html_does_not_double_wrap(self):
        page = read(self.page)
        out = build_pdf.print_html(page, {"title_page": {"title": "T"}}, "lbl")
        self.assertEqual(out.lower().count("<html"), 1)
        self.assertIn('<html data-theme="light"', out)
        self.assertNotIn("<script>", out)
        self.assertNotIn('" hidden>', out)
        self.assertIn('<div class="titlepage">', out)
        self.assertIn('<li class="lyr">GUIDES</li>', out)

    def test_bad_chrome_path_is_a_config_error(self):
        code, _, err = run(build_pdf.main, "--config", self.cfg, "--chrome", os.path.join(self.tmp, "nope.exe"))
        self.assertEqual(code, 2)
        self.assertIn("browser not found", err)


if __name__ == "__main__":
    unittest.main()
