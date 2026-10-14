# tali and masq: one voice, two surfaces

masq shapes how Claude talks in a session (interactive persona, hook-driven, stackable profiles with variants). tali shapes how documents read for their audiences (voice passes over prose, fidelity-verified, published as comparisons). The same voice can live on both surfaces without duplicating its definition.

## Using a masq profile as a tali voice

`voice-mutate` and `voice-review` accept a masq persona profile as a voice spec:

1. Locate the profile: `python ${CLAUDE_PLUGIN_ROOT}/tools/resolve_masq_profile.py <id>` prints the path of `profiles/<id>.md`. masq's root is not derivable from tali's own plugin root, so the script looks where an install actually lands, in order: `--root PATH` or `MASQ_PLUGIN_ROOT`; the install path recorded for masq in `~/.claude/plugins/installed_plugins.json` (a versioned cache directory that changes on every masq update, which is why it is read rather than hard-coded); then the marketplace clone under `~/.claude/plugins/marketplaces/masq`. Files beginning with `_` are templates, not profiles.
2. Treat the profile body plus the selected variant section as the persona guide's register and rules.
3. The profile's `scope` frontmatter still applies — a contextual profile that declares itself dormant outside its scope should not be used to voice-pass unrelated documents.
4. masq profiles carry no fidelity list (interactive chat does not need one; published documents do). The fidelity list always comes from the document set's voice profile, `tali.fidelity.json`, and its skeletons — build it there before the first pass.

Tone skills that follow the same shape (a skill with a `references/style-guide.md`, like afterdark) work the same way: the style guide is the register source, tali supplies the fidelity machinery. Scope declarations in those skills are respected the same as masq `scope` — a tone that limits itself to a content type is not applied outside it.

## Promoting a tali persona guide to a masq profile

The reverse direction: a persona guide written for documents (deltas from a base voice) can seed a masq profile by adding the frontmatter masq requires (`id`, `name`, `description`, `scope`, `default-variant`, `variants`) and splitting intensity levels into variant sections. Keep the two files linked by name in their headers so an update to one prompts a look at the other; they will still drift apart where the surfaces genuinely differ (channel calibration matters in chat; fidelity lists matter in documents).

## Voice versus conduct

A persona has two halves: voice (how its prose reads) and conduct (how it works as an agent — permission economy, evidence habits, reporting style). tali voice passes use only the voice half; a masq profile can carry both, so an interactive persona behaves and sounds consistent. Define the conduct half with `skills/voice-mutate/references/conduct-guide-template.md` and keep it beside the persona guide; it never applies to document rewrites.

## The de-tell pass on both surfaces

masq's `de-tell` profile and tali's `skills/voice-mutate/references/ai-ism-flags.md` describe the same catalogue of machine tells; `tools/check_tells.py` runs the mechanical half of that catalogue over documents. When the catalogue changes on one surface, the other is checked.

## Division of responsibility

| Concern | Owner |
| --- | --- |
| Interactive session tone, activation, stacking | masq |
| Document voice passes and de-tell | tali voice-mutate |
| Multi-voice rounds, verification, redlines | tali voice-review |
| Comparison sites and PDF manuals | tali voice-publish |
| Fidelity lists and fact skeletons | the document set's repo, via tali templates and `tali.fidelity.json` |
