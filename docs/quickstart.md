# Quickstart: a document set in a second voice

Ten steps from a directory of markdown to a published comparison, with a pass or fail check between the rewrite and the publish. `$T` is tali's `tools/` directory: `${CLAUDE_PLUGIN_ROOT}/tools` inside a Claude Code session, or `tools/` in a clone. The finished state of every step is in `examples/handbook/`.

## 1. Start from the sources

Your documents are markdown files under one directory, say `docs/`. Facts live here and nowhere else. Tables and registers that must never be voice-passed can sit alongside; the voice pass skips them and the publish step keeps them byte-identical in every voice.

## 2. Scaffold the project

```
python $T/init_site.py --sources docs --title "Team Handbook" --voices plain
```

This writes `handbook.html` (the page shell, already filled from your markdown), `tali.site.json` (publish config), and `tali.fidelity.json` (check config). Open `handbook.html` in a browser: the nav, the sections, and the prev/next pager work with no server. Nothing is overwritten on a rerun unless you pass `--force`.

## 3. Define the audience and the voice

Copy `skills/voice-review/references/audience-template.md` to `audiences.md` and fill one block per audience. Copy `skills/voice-mutate/references/voice-profile-template.md` to `voice-profile.md` and fill the fidelity list with the owner of the documents; that list is the contract every rewrite is checked against.

A persona variant is a delta from the base voice (`persona-guide-template.md`). To seed one from a masq profile, `python $T/resolve_masq_profile.py dean` prints the profile's path on this machine.

## 4. Write the fact skeletons

One per document, at `skeletons/<path>.skeleton.md`, in the format in `skills/voice-mutate/references/fact-skeleton-template.md`. They are built from the source before any rewriting. Items under Verbatim, Labels, Fixed phrases, and Qualifiers are enforced by the checker; Claims and Distinctions are for the verifier. Set-wide phrases (a label taxonomy, the policy boundary) go in `tali.fidelity.json` under `fidelity.all`.

## 5. Run the voice pass

In Claude Code, `/tali:voice-mutate` with the voice profile, writing each copy to `voices/plain/` at the same relative path as its source. The skill builds a skeleton if one is missing, rewrites, strips machine tells, self-checks, and has an independent agent cross-verify.

## 6. Check

```
python $T/check_fidelity.py            # PASS: n/n voice copies carry every fidelity item
python $T/check_tells.py voices/plain  # PASS: 0 strip, m review
```

A non-zero exit from the fidelity check means the pass is not finished. Fix the voice copy, or record an approved exception as a waiver with a reason in `tali.fidelity.json`. Never delete the item. The de-tell lint's `review` findings are for a human: an earned negation stays, a rhetorical one goes.

## 7. Publish

```
python $T/build_page.py --check && python $T/build_page.py
python $T/build_site.py
python $T/build_pdf.py
python $T/build_pdf.py --page site/plain.html --pdf handbook-plain.pdf
```

`site/` now holds `index.html` (original) and `plain.html`, joined by a switcher that keeps the reader on the same section. Deploy it to any static host; `skills/voice-publish/SKILL.md` has a Cloudflare Worker example. The PDF build needs Chrome, Edge, or Chromium; pass `--chrome PATH` if it is somewhere unusual.

## 8. Run the review round

The templates in `skills/voice-review/references/` carry the round: a round record (refs, passes, check output, findings), a change summary per voice, and a redline intake sheet that classifies every piece of feedback before anything is edited. A round closes when the fidelity check exits 0 for every voice and every finding row is resolved.

## 9. Branches instead of directories

If each voice lives on its own git branch at the same file paths (the pattern for large sets), point the checker at refs instead of directories:

```json
"sources_ref": "a1b2c3d",
"voices": { "casual": { "ref": "voice-casual" } }
```

and give the site config a `ref` per version (`tali.site.example.json` shows both forms). The check and the site then read from git, so a merge on main cannot change what is compared.

## 10. Keep it regenerable

Facts change in `docs/`, voice changes in the spec, and every voice copy is output. A fact correction re-runs the affected passes; a voice-rule change re-runs that voice; nothing is patched in a copy that touches the fidelity list.
