---
name: voice-mutate
description: This skill should be used when the user asks to rewrite a document or document set into a defined voice or for a target audience — "rewrite this in the plain voice", "do a voice pass on these docs", "adapt this for executives / new hires / engineers", "apply the persona guide to this", "de-AI this document", "run the de-tell pass" — or to define a new voice spec or persona guide for a document set. Facts, labels, and policy meaning never change; only the prose does.
version: 0.1.0
---

# Voice mutate

Rewrite prose into a defined voice while preserving every fact, label, number, qualifier, and distinction the source carries. Voice is downstream of accuracy: a rewrite that blurs one fidelity item is wrong no matter how well it reads.

## Inputs

Establish these before touching prose. Ask only for what cannot be inferred:

1. **Source**: the file(s) or text to rewrite. For a document set, list the files that get the voice pass and the files that stay untouched (reference tables, registers, generated output).
2. **Voice spec**: one of
   - a project voice-profile file (create one from `references/voice-profile-template.md` if none exists);
   - a persona guide (create from `references/persona-guide-template.md`);
   - a masq persona profile — resolve by id from the installed masq plugin (`profiles/<id>.md` under the masq plugin root) and treat its body plus selected variant as the persona guide;
   - a tone skill's style guide (e.g., an afterdark-style skill's `references/style-guide.md`).
3. **Fidelity list**: what never changes. If the voice spec has no fidelity list, build one with the owner before rewriting (categories and procedure in `references/fidelity-checklist.md`).

## Procedure

Per file, in order — do not merge the steps:

1. **Fact skeleton.** Extract every claim, number, name, label, qualifier, and distinction into a flat list (`references/fidelity-checklist.md`). This happens before any rewriting so the skeleton cannot be contaminated by the rewrite.
2. **Rewrite.** Apply the voice spec: compression plus voice in one pass. Preserve verbatim everything on the fidelity list — code, paths, commands, tables, defined labels, load-bearing qualifiers.
3. **De-tell pass.** Strip AI-isms and rhetorical negation-contrasts per `references/ai-ism-flags.md`. Load-bearing negations stay.
4. **Self-check.** Walk the fact skeleton against the rewrite. Every skeleton item must survive with its meaning intact.
5. **Cross-verify.** For anything beyond a single small file, have an independent agent (fresh context, no sight of the rewrite reasoning) verify the rewrite against the skeleton using the checklist in `references/fidelity-checklist.md`. Fix fidelity breaks in the rewrite — never by weakening the skeleton.
6. **Run the fidelity check.** When the document set has a `tali.fidelity.json`, run `python ${CLAUDE_PLUGIN_ROOT}/tools/check_fidelity.py --config <path>` and treat a non-zero exit as an unfinished pass. It proves the verbatim items survived; steps 4 and 5 still cover meaning drift.

For document sets, run files through this pipeline independently (subagents in parallel are fine); collect cross-verification findings and fix before declaring the pass complete.

## Scope discipline

- Rewrite only the files in scope. Reference layers, tables, and generated artifacts stay byte-identical unless the owner says otherwise.
- One voice per pass. Producing a second voice is a second pass (or use the voice-review skill for the full multi-voice round).
- If the source contains an error, flag it to the owner; do not silently fix facts during a voice pass — that contaminates the diff.

## Defining a new voice

- Base voice for a document set: instantiate `references/voice-profile-template.md`, fill the fidelity list with the owner, commit it beside the documents it governs.
- Persona variant: instantiate `references/persona-guide-template.md` as deltas from the base voice. A masq profile can seed it; keep the document-facing guide in the repo that owns the documents, and keep the interactive persona in masq — same voice, two surfaces (see `docs/masq-integration.md` in this plugin).
- Agent conduct (how a persona works, not how it reads): define separately with `references/conduct-guide-template.md`. Conduct never applies to document rewrites; it exists so a masq profile can carry a consistent voice-plus-conduct persona for interactive sessions.
