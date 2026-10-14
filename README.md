# tali

Documents and content shaped for the people who will read them. tali packages a voice-mutation and multi-voice publishing workflow as a Claude Code plugin: rewrite a document set into defined voices for target audiences, verify that no fact, label, or qualifier changed, and publish the results as a comparison site and PDF manuals.

Named for Taliesin, the bard who shaped the same material for whatever court he addressed.

## Skills

| Skill | Use it for |
| --- | --- |
| `/tali:voice-mutate` | Rewrite a document (or set) into one defined voice: fact skeleton → rewrite → de-tell pass → fidelity verification, gated by the fidelity check and the de-tell lint. Also defines new voice profiles and persona guides from templates. |
| `/tali:voice-review` | The full multi-voice round: audiences → voice specs → parallel passes → adversarial verification → comparison and redline artifacts → redline intake, with templates for the audience definition, the round record, the per-voice change summary, and the intake sheet. |
| `/tali:voice-publish` | Build the outputs: a scaffolded page shell, markdown-driven HTML sections, a multi-version site with a voice switcher (versions from git refs or voice directories), and a print-ready PDF manual per voice. |

## The model

- **Source × spec = voice copy.** Facts change only in the source prose; voices change only in voice specs; every voice copy is regenerable output.
- **Fidelity is enforced, not hoped for.** Each document set declares a fidelity list (labels, taxonomies, paths, numbers, load-bearing qualifiers, distinctions) in its voice profile, its `tali.fidelity.json`, and one fact-skeleton file per document. Every pass builds the skeleton first and is cross-verified against it by independent agents, and `tools/check_fidelity.py` reruns the verbatim half as a pass or fail check.
- **Versions live in git refs.** The original prose is pinned to a commit, persona variants to branches (or to directories, for small sets), so comparisons survive merges.
- **Interactive personas interoperate.** A masq profile or a tone skill's style guide can serve as a voice spec; see `docs/masq-integration.md`.

## Start here

`docs/quickstart.md` goes from a directory of markdown to a published two-voice comparison in ten steps. `examples/handbook/` is the finished state of those steps: three documents, a filled-in voice profile and audience definition, fact skeletons, a plain-voice copy, and the configs, all checked and built by the test suite.

## Install

```
/plugin marketplace add mdn87/tali
/plugin install tali@tali
```

Or from a local clone: `/plugin marketplace add C:\path\to\tali`. While the repository is private, the machine doing the install needs GitHub credentials that can read it (`gh auth login` or a git credential helper); otherwise the marketplace add fails before anything is downloaded.

## Tools

`tools/` holds stdlib-only Python scripts, Python 3.12 or newer, every one with `--help`, exit 0 on success and 2 on a config error:

| Script | Does |
| --- | --- |
| `init_site.py` | Scaffold a page shell (from `tali.page.template.html`), `tali.site.json`, and `tali.fidelity.json` from a markdown directory, filled on the spot. |
| `build_page.py` | Refill the page's sections from markdown; `--check` reports without writing. |
| `build_site.py` | Assemble the multi-version site with the switcher, from git refs and voice directories. |
| `build_pdf.py` | Render a page or one built version to PDF with headless Chrome, Edge, or Chromium (`--chrome PATH` if it is not on a usual path). |
| `check_fidelity.py` | The fidelity check: exit 0 when every voice copy carries the source's code, URLs, numbers, declared phrases, and skeleton items; 1 on any break. Reads directories or git refs. |
| `check_tells.py` | The de-tell lint: `strip` findings fail (exit 1), `review` findings are for a human (`--strict` fails them too). |
| `resolve_masq_profile.py` | Print the path of an installed masq profile so it can serve as a voice spec. |

`tali.site.example.json` and `tali.fidelity.example.json` document every config key.

Tests: `python -m unittest discover -s tests` (the PDF test skips when no browser is installed). CI runs them on Ubuntu, Windows, and macOS.

## Provenance

Extracted and generalized from a production multi-voice documentation round (26 staff-facing documents × 3 voices with verified fidelity, comparison site, and PDF manuals). The domain content stayed home; the machinery is here. `CHANGELOG.md` lists what has changed since.
