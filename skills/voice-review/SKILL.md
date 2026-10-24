---
name: voice-review
description: This skill should be used when the user wants the full multi-voice production round on a document set — "run the multi-voice pass", "produce the plain and casual versions", "adapt this doc set for each audience", "set up a redline round", "regenerate the voices and compare" — covering audience definition, per-voice rewrite passes, adversarial fidelity verification, and comparison/redline artifacts. Also use for audience tiers that vary coverage, reading level and technical depth. For one edition of one document, use voice-mutate instead.
version: 0.3.0
---

# Voice review

Run a document set through the full multi-voice production round: define the audiences, define or select a voice per audience, rewrite in parallel, adversarially verify fidelity, and produce the artifacts a human review round needs. This is the orchestration layer over voice-mutate's per-file pipeline.

When the user wants different depth or length, treat the outputs as audience editions. Read [the audience-adaptation procedure](../voice-mutate/references/audience-adaptation.md) and choose sensible tiers yourself. Do not constrain a beginner summary to the same facts, headings and length as a technical explanation. Record selective coverage explicitly while keeping the source and full skeleton intact.

## The round, stage by stage

1. **Inventory and scope.** List every document in the set. Split it three ways with the owner: voice-passed files (audience-facing prose), reference files (tables, registers, crosswalks — never voice-passed), and generated output (rebuilt, never hand-edited). Record the split in the round record (`references/round-record-template.md`); it is the scope contract for every later stage.

2. **Audiences and voices.** For each target audience, fill one block of `references/audience-template.md`: who they are, what they need from the documents, what they already know, what they are likely to misread, the voice that serves them, and an acceptance test. Map each audience to a voice spec:
   - base voice: a voice-profile instantiated from the voice-mutate references, with the fidelity list filled in;
   - persona variants: persona guides written as deltas from the base voice (a masq profile can seed one);
   - the original prose is itself a version — pin it to a git ref so it survives merges.

3. **Baseline pin.** Before the first pass, commit the current prose and record the ref. Comparison versions come from git refs, not saved copies; a merge cannot silently rewrite history that a ref pins. That same ref is the `sources_ref` in `tali.fidelity.json` when voices live on branches.

4. **Voice passes.** One pass per voice, each pass using the full-coverage voice-mutate pipeline or the audience-adaptation procedure selected in its audience contract. Run files within a pass as parallel subagents; run voices as separate passes. Voices can live as directories (`voices/<voice>/`, the layout `tools/init_site.py` sets up) or as branches at the source's own paths (a branch per persona variant keeps the git-ref versioning clean); the checker and the site build read both.

5. **Adversarial verification.** Spawn independent verifiers for each pass with source, full skeleton, coverage contract and copy, without writer reasoning. Check permission/effectiveness drift, enumeration scope, qualifiers, distinctions, unsupported additions and misleading omissions. Fix findings and re-verify. Full-coverage copies must pass `${CLAUDE_PLUGIN_ROOT}/tools/check_fidelity.py` with their unchanged full-source config. Selective summaries use the audience-adaptation coverage review; do not claim the all-items checker passed them. All copies must have no unresolved `strip` findings from `tools/check_tells.py`. Separately assess whether voices are distinguishable, or depth tiers provide different selection and explanation, according to the request. Word-count differences alone do not establish success.

6. **Comparison and redline artifacts.** Produce what the human round needs:
   - a comparison site with a version switcher (voice-publish skill): preserve shared sections where they exist; for different depth tiers, map shared topics or return to the edition's start;
   - a print/PDF manual per voice for redline markup (`build_pdf.py --page site/<voice>.html --pdf <name>.pdf`);
   - a change summary per voice from `references/change-summary-template.md`: what moved, what was compressed, what the verifier flagged and how it was resolved.

7. **Redline intake.** When marked-up feedback comes back, classify each item on a `references/redline-intake-template.md` sheet before editing anything: fact correction (fix in the source, then re-run affected voice passes — never patch a voice copy directly), voice-rule change (update the voice spec, re-run its pass), or one-off phrasing (fix in the voice copy only if it does not touch the fidelity list). The source of truth is the source prose plus the voice specs — voice copies are always regenerable.

## Invariants

- Facts change only in the source, voices change only in the specs, and every voice copy is disposable output of (source × spec).
- Reference files are byte-identical across all voices.
- Full-coverage voices retain the entire fidelity contract. Selective editions follow their recorded coverage contracts; every retained claim remains accurate and qualified, with material limitations preserved. Neither mode changes source facts.
- Keep a record per round in `references/round-record-template.md`: refs compared, passes run, fidelity check output, verifier findings, resolutions. The next round starts from that record.

## References

- `references/audience-template.md` — one block per audience, plus a coverage table.
- `references/round-record-template.md` — the per-round record; a round is closed by its last section's conditions.
- `references/change-summary-template.md` — per voice, per round.
- `references/redline-intake-template.md` — classification rules and the intake table.
