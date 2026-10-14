# tali completeness review, 2026-10-13

Scope: every file in the repository at commit `187911f` (`24a173f` before the commit-email rewrite of 2026-10-14), plus live probes of the tools and the local plugin install. Nothing was changed in the plugin; this is a report.

Status, 2026-10-14: all thirteen items are closed. Items 1 to 3 and 5 to 13 shipped in version 0.2.0 (see `CHANGELOG.md`); for item 4 the repository was made public and the local install updated to 0.2.0.

## What was probed and holds up

- `claude plugin validate` passes on both `.claude-plugin/marketplace.json` and `.claude-plugin/plugin.json`.
- The publish pipeline runs end to end on a fresh project that never saw the origin campaign. In a scratch directory with a hand-written page shell, two markdown sources, a cover file, and a `tali.site.json`, `build_page.py --check` and `build_page.py` exited 0; `build_site.py` exited 0 and wrote three versions, one from the working tree (`ref: null`), one from a commit (`HEAD`), one from a branch (`voice-casual`); the casual cover swap landed only in `casual.html`; the four-column table was marked `tablewrap wide`; `build_pdf.py` exited 0 and wrote a 114,417-byte PDF through headless Chrome or Edge.
- `python -m unittest discover -s tests` passes 12 of 12 for `check_fidelity.py`.
- The Dias board parses clean with `parseChipFile`, `parseProjectStatusFile`, and `chipFileProblems(…, 'tali')`.

## Features left to build, ranked by what they block

### Tier 1: blocks reuse on a second campaign

1. **A page-shell template or scaffold for voice-publish.** The three scripts require an HTML shell that already exists with `<div class="brand">`, `<div class="sub">`, `<nav class="side">` containing `grp-label` and `navlink` elements, `<section class="doc" id="doc-…">` blocks with a `<p class="crumb">`, and a `<style>` block. The switcher CSS that `build_site.py` injects also depends on CSS custom properties the shell must define (`--line`, `--surface`, `--accent`, `--accent-wash`, `--accent-ink`, `--muted`, `--ink`) and on the Public Sans and IBM Plex Mono fonts. None of this ships. To run the probe I reverse-engineered the shell from `build_site.py`. A new project cannot publish without doing the same. This is the largest single gap.
2. **Fidelity check over git refs.** `voice-review` keeps each voice on its own branch and pins the original to a commit, but `check_fidelity.py` only reads voice copies from directories. There is no way to point it at `voice-casual:docs/` without first exporting the branch by hand. Either the checker learns a per-voice `ref`, or the skills document an export step. This gap was introduced by the 2026-10-13 work and is not covered by its tests.
3. **Quickstart and a worked example.** There is no end-to-end walkthrough for a fresh project: define audiences, fill a voice profile, run a pass, run the check, build the site. The only filled-in voice profile and fidelity list in the repo is the test fixture under `tests/fixtures/fidelity/`, which is sized for the unit tests, not for learning from.
4. **Distribution.** The GitHub repository is private (`gh repo view mdn87/tali` reports `PRIVATE`), so `/plugin marketplace add mdn87/tali` only works for a machine signed in to GitHub as the owner. The chip `tali:marketplace-install` says the repo was pushed to a public remote; that claim is wrong. The authoring machine's own install (`installed_plugins.json`, `tali@tali`) sits at commit `db04f5e` (`35d5909` before the rewrite), installed 2026-08-30, and its `tools/` directory holds only the three build scripts, so even here the installed plugin predates `check_fidelity.py`. No plugin update has been run since.

### Tier 2: turns agent judgment into repeatable artifacts

5. **A fact-skeleton file format.** The skeleton is the contract every pass is verified against, yet nothing defines what it looks like on disk. It cannot be stored beside the documents, diffed between rounds, or handed to a verifier as a file. A format (likely one markdown or JSON file per source document) would also let `check_fidelity.py` consume it instead of a hand-maintained phrase list.
6. **Templates for the round's named deliverables.** `voice-review` requires an audience definition, a per-round record (refs compared, passes run, check output, verifier findings, resolutions), a change summary per voice, and a redline-intake classification. `references/` has none of these; it holds only the voice profile, persona guide, conduct guide, fidelity checklist, and AI-ism flags.
7. **A de-tell lint.** The "strip on sight" list in `ai-ism-flags.md` is a fixed vocabulary and can be checked mechanically, with the negation-contrast and rhetorical-question patterns flagged for human judgment. Today the de-tell pass is entirely agent judgment with no pass or fail output.
8. **masq profile resolution.** `voice-mutate` says to resolve a masq profile from `profiles/<id>.md` under the masq plugin root, but gives no way to locate that root (`${CLAUDE_PLUGIN_ROOT}` is tali's own root). On this machine the profiles live at `~/.claude/plugins/cache/masq/masq/0.7.0/profiles/`, a path that changes with every masq version.

### Tier 3: robustness of the existing tools

9. **Markdown converter gaps in `build_page.py`**, each observed in the probe output:
   - nested list items are flattened into siblings;
   - image syntax `![alt](src)` renders as the literal text `!alt`;
   - a `---` horizontal rule renders as a paragraph containing `---`;
   - headings deeper than `####` render as a literal paragraph;
   - a list whose items are separated by blank lines becomes one list per item;
   - a link to a mapped file with a fragment, such as `README.md#section`, maps to the file's anchor and drops the fragment;
   - a missing markdown source raises a raw `FileNotFoundError` traceback, in `--check` mode too, instead of a clean message.
10. **`build_pdf.py` portability.** `CHROME_CANDIDATES` lists two Windows paths and two Linux paths; there is no macOS path and no `--chrome PATH` override, so the PDF build fails out of the box on macOS, which the workspace instructions name as a possible environment. Chrome's exit status is not checked; the script only tests whether the PDF file appeared.
11. **Build-tool tests and CI.** Only `check_fidelity.py` has tests. The three build scripts have none, there is no `.github/workflows`, and the converter gaps above would have been caught by a fixture like the one used for this probe.
12. **Versioning hygiene.** `plugin.json` is still `0.1.0` after the fidelity-check feature; there is no changelog; `skills/voice-publish/SKILL.md` lacks the `version` frontmatter that the other two skills carry.
13. **Small code issues.** `build_site.py` discards git's stderr, so a bad ref or a missing `git` binary gives a skipped version or a traceback with no reason. `build_pdf.py` duplicates `_strip_comments` and `load_config` from `build_page.py` instead of importing them.

## Board implications

The current next step, `tali:install-outside-origin`, cannot complete as written until item 4 is resolved, because a machine that never held the clone needs either a public repo or GitHub credentials for the private one. The step after it, `tali:second-campaign-reuse`, is blocked by item 1 on the publish side and by item 3 for anyone other than the author. Items 5 through 8 are what the originating round did by hand and would need doing by hand again on a second campaign.

## Residuals

- Exit code of `build_page.py` on a missing source was not captured cleanly (the probe's `$?` reflected a pipe), so only the traceback is confirmed.
- Nothing was probed on macOS or Linux; the portability finding comes from reading the candidate list.
- The skills themselves were not run against a real document in this session; their gaps come from reading the skill text and the references.
- The report file is not committed.
