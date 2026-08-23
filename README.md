# tali

Documents and content shaped for the people who will read them. tali packages a voice-mutation and multi-voice publishing workflow as a Claude Code plugin: rewrite a document set into defined voices for target audiences, verify that no fact, label, or qualifier changed, and publish the results as a comparison site and PDF manuals.

Named for Taliesin, the bard who shaped the same material for whatever court he addressed.

## Skills

| Skill | Use it for |
| --- | --- |
| `/tali:voice-mutate` | Rewrite a document (or set) into one defined voice: fact skeleton → rewrite → de-tell pass → fidelity verification. Also defines new voice profiles and persona guides from templates. |
| `/tali:voice-review` | The full multi-voice round: audiences → voice specs → parallel passes → adversarial verification → comparison and redline artifacts → redline intake. |
| `/tali:voice-publish` | Build the outputs: markdown-driven HTML sections, a multi-version site with a voice switcher (versions pulled from git refs), and a print-ready PDF manual with auto-generated TOC. |

## The model

- **Source × spec = voice copy.** Facts change only in the source prose; voices change only in voice specs; every voice copy is regenerable output.
- **Fidelity is enforced, not hoped for.** Each document set declares a fidelity list (labels, taxonomies, paths, numbers, load-bearing qualifiers, distinctions). Every pass builds a fact skeleton first and is cross-verified against it by independent agents.
- **Versions live in git refs.** The original prose is pinned to a commit, persona variants to branches, so comparisons survive merges.
- **Interactive personas interoperate.** A masq profile or a tone skill's style guide can serve as a voice spec; see `docs/masq-integration.md`.

## Install

```
/plugin marketplace add mdn87/tali
/plugin install tali@tali
```

Or from a local clone: `/plugin marketplace add C:\path\to\tali`.

## Tools

`tools/` holds the three config-driven build scripts used by voice-publish (`build_page.py`, `build_site.py`, `build_pdf.py`) and `tali.site.example.json` documenting the config. Python 3.12+, stdlib only; PDF rendering uses headless Chrome or Edge.

## Provenance

Extracted and generalized from a production multi-voice documentation round (26 staff-facing documents × 3 voices with verified fidelity, comparison site, and PDF manuals). The domain content stayed home; the machinery is here.
