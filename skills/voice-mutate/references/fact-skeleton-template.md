# Fact Skeleton — Template and File Format

Purpose: the on-disk shape of a fact skeleton, so it can be committed beside the documents, diffed between rounds, handed to a verifier as a file, and read by `tools/check_fidelity.py`.

One skeleton per source document, written before any rewriting, from the source only. Location: `<skeletons_dir>/<path>.skeleton.md`, mirroring the source tree with `.md` replaced by `.skeleton.md` (so `docs/guides/setup.md` has `skeletons/guides/setup.skeleton.md`). `skeletons_dir` is set in `tali.fidelity.json`.

## The file

```markdown
# Fact skeleton: guides/setup.md

## Claims
- C1: Uploads only work while the sync service is running.
- C2: The desktop app does not read the config file.

## Verbatim
- V1: `npm ci`
- V2: `tali-agent --port 8080`
- V3: `~/.tali/config.toml`
- V4: 8080

## Labels
- L1: Sev-1
- L2: Sev-2

## Fixed phrases
- F1: public or fully synthetic data

## Qualifiers
- Q1: only when the sync service is running
- Q2: reduces exposure but is not a sandbox

## Distinctions
- D1: the CLI reads the config file; the desktop app does not
- D2: hosted service vs local install (never merged into "the service")
```

## Rules

- Every bullet is `- <ID>: <text>`. IDs are a capital letter prefix and a number (`C1`, `V3`, `Q2`), unique within the file, and never renumbered once a round has referenced them.
- **Claims** are what the document asserts, in the skeleton author's words. Verifiers walk them by hand; the checker ignores them.
- **Verbatim**, **Labels**, **Fixed phrases**, and **Qualifiers** are copied from the source character for character (backticks around code are allowed and stripped). `check_fidelity.py` requires each of them to appear in every voice copy of this document, whitespace and `*` emphasis aside, and refuses to run if one is no longer in the source, because then the skeleton has drifted from the document it describes.
- **Distinctions** name the pairs the source keeps separate, in a form a reader can check. The checker ignores them because a distinction can survive in different words; the verifier confirms both members are still distinguishable.
- Section headings are matched case-insensitively; a section can be left out when it has no items. Anything outside these six sections is a note for humans.

## Keeping it honest

The skeleton only changes when it misread the source, and that is verified against the source, never against a rewrite. A fidelity break is fixed in the voice copy or recorded as a waiver with a reason in `tali.fidelity.json`; deleting the item from the skeleton to make the check pass defeats the procedure.
