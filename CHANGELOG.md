# Changelog

## 0.3.0 — 2026-10-23

### Added
- Audience-adaptation procedure for selective summaries, beginner explanations, decision briefs and supported technical expansion, with explicit coverage and reading budgets.
- Independent checks for essential coverage, included assertions, misleading omissions, supported explanations and useful differences in depth.

### Changed
- Skills distinguish full-coverage voice rewrites from audience editions. The source skeleton stays intact; selective summaries no longer inherit an inappropriate requirement to repeat every literal source item.
- Audience, round and change-summary templates record depth, deferred detail, explanation support and actual validation scope. Publication guidance permits different structures across tiers.
- The existing fidelity checker remains unchanged and mandatory for full-coverage copies. It is not presented as a summary validator.

## 0.2.0 — 2026-10-13

The gaps from the 2026-10-13 completeness review (`docs/completeness-2026-10-13.md`), closed.

### Added
- `tools/check_fidelity.py`: a rerunnable fidelity check with pass or fail exit status; reads voices from directories or git refs (`sources_ref`, per-voice `ref`) and consumes fact-skeleton files (`skeletons_dir`).
- `tools/check_tells.py`: a de-tell lint mirroring `ai-ism-flags.md`; `strip` findings fail, `review` findings need a human (`--strict` fails them too).
- `tools/init_site.py` and `tools/tali.page.template.html`: scaffold a page shell, `tali.site.json`, and `tali.fidelity.json` from a directory of markdown, filled on the spot.
- `tools/resolve_masq_profile.py`: locate a masq profile from the plugin install records.
- `skills/voice-mutate/references/fact-skeleton-template.md`: the on-disk skeleton format.
- `skills/voice-review/references/`: audience, round-record, change-summary, and redline-intake templates.
- `examples/handbook/`: a three-document, two-voice worked example that the tests check and build.
- `docs/quickstart.md`, `tests/` (74 tests), `.github/workflows/test.yml` (Ubuntu, Windows, macOS; Python 3.12 and latest).

### Changed
- `build_page.py`: nested lists, blank lines between list items, horizontal rules, headings to h6 with ids (`<section>--<slug>`), images, links that keep their fragment, clean exit 2 on a missing source, `rebuild()` for reuse.
- `build_site.py`: versions may name a `sources_root` (directory voices) as well as a `ref`; a missing voice directory or a bad ref is skipped with the reason; charset tag lands inside `<head>`; switcher script lands before `</body>`.
- `build_pdf.py`: browser lookup covers Windows, macOS, Linux and PATH, with `--chrome` and `TALI_CHROME`; `--page` and `--pdf` render one voice; a full HTML document is no longer wrapped in a second one; the switcher bar is hidden in print; a render failure reports the browser's exit and stderr.
- Skills: the fidelity check is the required gate in voice-mutate and voice-review; voice-publish documents the scaffold and the new config forms; masq resolution is specified.
- All three skills and the plugin are versioned 0.2.0.

## 0.1.0 — 2026-08-23

Initial plugin: voice-mutate, voice-review, voice-publish skills; `build_page.py`, `build_site.py`, `build_pdf.py`; masq integration note.
