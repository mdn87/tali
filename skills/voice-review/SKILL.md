---
name: voice-review
description: This skill should be used when the user wants the full multi-voice production round on a document set — "run the multi-voice pass", "produce the plain and casual versions", "adapt this doc set for each audience", "set up a redline round", "regenerate the voices and compare" — covering audience definition, per-voice rewrite passes, adversarial fidelity verification, and comparison/redline artifacts. For a single-voice rewrite of one document, use voice-mutate instead.
version: 0.1.0
---

# Voice review

Run a document set through the full multi-voice production round: define the audiences, define or select a voice per audience, rewrite in parallel, adversarially verify fidelity, and produce the artifacts a human review round needs. This is the orchestration layer over voice-mutate's per-file pipeline.

## The round, stage by stage

1. **Inventory and scope.** List every document in the set. Split it three ways with the owner: voice-passed files (audience-facing prose), reference files (tables, registers, crosswalks — never voice-passed), and generated output (rebuilt, never hand-edited). Record the split; it is the scope contract for every later stage.

2. **Audiences and voices.** For each target audience, name the reader, what they need from the documents, and the voice that serves them. Map each audience to a voice spec:
   - base voice: a voice-profile instantiated from the voice-mutate references, with the fidelity list filled in;
   - persona variants: persona guides written as deltas from the base voice (a masq profile can seed one);
   - the original prose is itself a version — pin it to a git ref so it survives merges.

3. **Baseline pin.** Before the first pass, commit the current prose and record the ref. Comparison versions come from git refs, not saved copies; a merge cannot silently rewrite history that a ref pins.

4. **Voice passes.** One pass per voice, each pass running the voice-mutate pipeline per file (fact skeleton → rewrite → de-tell → self-check). Run files within a pass as parallel subagents; run voices as separate passes or separate branches (a branch per persona variant keeps the git-ref versioning clean).

5. **Adversarial verification.** For each voice pass, spawn independent verifier agents that see only the source, the fact skeleton, and the rewrite — not the rewrite reasoning. They check the fidelity checklist: permission-vs-effectiveness drift, dropped enumerations, opened closed-lists, weakened qualifiers, blurred distinctions. Findings are fixed in the rewrite and re-verified. A pass completes when verification comes back clean, not when the rewrite finishes.

6. **Comparison and redline artifacts.** Produce what the human round needs:
   - a comparison site with a version switcher (voice-publish skill) so a reviewer can flip voices while staying on the same section;
   - a print/PDF manual per voice for redline markup;
   - a change summary per voice: what moved, what was compressed, what the verifier flagged and how it was resolved.

7. **Redline intake.** When marked-up feedback comes back, classify each item: fact correction (fix in the source, then re-run affected voice passes — never patch a voice copy directly), voice-rule change (update the voice spec, re-run its pass), or one-off phrasing (fix in the voice copy only if it does not touch the fidelity list). The source of truth is the source prose plus the voice specs — voice copies are always regenerable.

## Invariants

- Facts change only in the source, voices change only in the specs, and every voice copy is disposable output of (source × spec).
- Reference files are byte-identical across all voices.
- Fidelity items (labels, taxonomies, qualifiers, distinctions, code, paths, numbers) are verbatim-identical across all voices — this is what the verifiers exist to prove.
- Keep a record per round: refs compared, passes run, verifier findings, resolutions. The next round starts from that record.
