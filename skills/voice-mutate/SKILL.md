---
name: voice-mutate
description: This skill should be used when the user asks to rewrite a document or document set into a defined voice or for a target audience — "rewrite this in the plain voice", "do a voice pass on these docs", "adapt this for executives / new hires / engineers", "apply the persona guide to this", "de-AI this document", "run the de-tell pass" — or to create audience summaries, beginner explanations, deeper technical editions, or voice specs. Selective coverage is explicit; factual meaning never changes.
version: 0.3.0
---

# Voice mutate

Shape prose for its reader while preserving factual meaning and the limits of every retained claim. Choose the coverage mode before drafting:

- **Full-coverage voice rewrite:** retain every fact, label, number, qualifier and distinction. Use the procedure below. This remains the default for a request to change tone or voice.
- **Audience adaptation:** for summaries, beginner explanations, different detail levels or technical expansion, read [references/audience-adaptation.md](references/audience-adaptation.md). Select and explain material according to a recorded audience contract. Keep the source and complete skeleton unchanged; record omissions and support added explanation.

Infer sensible tiers from the request and proceed. Do not require the user to choose routine tone, length or presentation details. A request for a short beginner summary authorizes selective coverage, but not hiding a limitation that changes the meaning of a retained claim.

## Inputs

Establish these before touching prose. Ask only for what cannot be inferred:

1. **Source**: the file(s) or text to rewrite. For a document set, list the files that get the voice pass and the files that stay untouched (reference tables, registers, generated output).
2. **Voice spec**: one of
   - a project voice-profile file (create one from `references/voice-profile-template.md` if none exists);
   - a persona guide (create from `references/persona-guide-template.md`);
   - a masq persona profile — locate it with `python ${CLAUDE_PLUGIN_ROOT}/tools/resolve_masq_profile.py <id>`, which prints the path of `profiles/<id>.md` from the masq install records (or `--root PATH` / `MASQ_PLUGIN_ROOT` when masq lives elsewhere), and treat its body plus the selected variant as the persona guide;
   - a tone skill's style guide (e.g., an afterdark-style skill's `references/style-guide.md`).
3. **Fidelity list**: what never changes. If the voice spec has no fidelity list, build one with the owner before rewriting (categories and procedure in `references/fidelity-checklist.md`). The mechanical half lives in the document set's `tali.fidelity.json` and its fact skeletons, so `tools/check_fidelity.py` can enforce it.

## Full-coverage procedure

Per file, in order — do not merge the steps:

1. **Fact skeleton.** Extract every claim, number, name, label, qualifier, and distinction into a flat list and write it to `skeletons/<path>.skeleton.md` in the format in `references/fact-skeleton-template.md`. This happens before any rewriting so the skeleton cannot be contaminated by the rewrite. Verbatim, Labels, Fixed phrases, and Qualifiers are what the checker enforces; Claims and Distinctions are what the verifier judges.
2. **Rewrite.** Apply the voice spec: compression plus voice in one pass. Preserve verbatim everything on the fidelity list — code, paths, commands, tables, defined labels, load-bearing qualifiers. Write the copy to the voice's directory at the same relative path as the source (`voices/<voice>/<path>`), or to the voice's branch at the source's own path.
3. **De-tell pass.** Strip AI-isms and rhetorical negation-contrasts per `references/ai-ism-flags.md`. Load-bearing negations stay. Then run `python ${CLAUDE_PLUGIN_ROOT}/tools/check_tells.py <voice copy>`: a `strip` finding means the pass is not done; a `review` finding is a negation or question to judge by the test in the reference, and an earned one stays.
4. **Self-check.** Walk the fact skeleton against the rewrite. Every skeleton item must survive with its meaning intact.
5. **Cross-verify.** For anything beyond a single small file, have an independent agent (fresh context, no sight of the rewrite reasoning) verify the rewrite against the skeleton file using the checklist in `references/fidelity-checklist.md`. Fix fidelity breaks in the rewrite — never by weakening the skeleton.
6. **Run the fidelity check.** `python ${CLAUDE_PLUGIN_ROOT}/tools/check_fidelity.py --config <tali.fidelity.json>` reads the skeletons, the declared phrases, and every code span, URL, and number in the source, and exits 0 only when every voice copy carries all of them. A non-zero exit is an unfinished pass. It proves the verbatim items survived; steps 4 and 5 still cover meaning drift.

For document sets, run files through this pipeline independently (subagents in parallel are fine); collect cross-verification findings and fix before declaring the pass complete.

## Scope discipline

- Rewrite only the files in scope. Reference layers, tables, and generated artifacts stay byte-identical unless the owner says otherwise.
- One voice per pass. Producing a second voice is a second pass (or use the voice-review skill for the full multi-voice round).
- If the source contains an error, flag it to the owner; do not silently fix facts during a voice pass — that contaminates the diff.

## Defining a new voice

- Base voice for a document set: instantiate `references/voice-profile-template.md`, fill the fidelity list with the owner, commit it beside the documents it governs. Put the set-wide verbatim items (label taxonomies, fixed phrases) in `tali.fidelity.json` under `fidelity.all`; `tools/init_site.py` creates that file alongside the publish config, and `tools/tali.fidelity.example.json` documents every key.
- Persona variant: instantiate `references/persona-guide-template.md` as deltas from the base voice. A masq profile can seed it; keep the document-facing guide in the repo that owns the documents, and keep the interactive persona in masq — same voice, two surfaces (see `docs/masq-integration.md` in this plugin).
- Agent conduct (how a persona works, not how it reads): define separately with `references/conduct-guide-template.md`. Conduct never applies to document rewrites; it exists so a masq profile can carry a consistent voice-plus-conduct persona for interactive sessions.

A complete small setup, with skeletons, a filled profile, and passing checks, is in `examples/handbook/`; `docs/quickstart.md` walks through building one.
