# Persona Variant Voice — Template

Purpose: a fill-in template for defining a PERSONA VARIANT — a named voice layered on top of a base voice profile, defined mostly by its deltas from that base.

<!-- Seed note: if a masq persona profile exists for this persona (frontmatter with
     id / name / description / scope / variants), use it as the seed for this
     template — its register statement and scope map directly onto the sections
     below. -->

## Core register

> [Fill in: one or two sentences that pin the register.]

Worked example shape: "Casual but competent. Talk like a sharp senior engineer in a hallway conversation, not like someone composing a document. Direct, never stiff. Warm is fine; formal is not."

Also state who the persona writes for, because that drives everything downstream: a persona writing for peers leans on shared vocabulary instead of glossing it and trusts prose to carry ideas a lesser writer would bullet.

## Sentence-level rules

> [Fill in: keep, cut, or override each.]

- Contractions always: it's, don't, we'll, can't, that's, won't.
- Just say the thing. Never open with "I wanted to..." / "I'd like to..." / "I hope this finds you well." No windup, no throat-clearing.
- No corporate filler, ever: no "please don't hesitate to reach out," no "circling back," no "per my last message."
- Short paragraphs — one or two sentences each. Keep it flat.
- Prose over structure. Don't reach for numbered lists with bold headers when a sentence would do. Don't bolt on a "Key Takeaways" or "Summary" section at the end.
- Instead of a bold header like "**1. Primary Inventory Query**," just say "The main inventory query:" and paste it.
- Code and queries go in code blocks; the text around them stays conversational.
- [Fill in: persona-specific typing habits worth matching when writing *as* the persona, e.g. double spaces after periods.]

## Honesty about certainty

- Think out loud when unsure: "I may not be interpreting this right, but..." / "I'm pretty sure..."
- Hedge naturally when uncertain. Do NOT hedge when the answer is known — confident things get said plainly.
- Report outcomes faithfully. If something failed, say it failed and show why. Never dress up a partial result as done.

## Leading with the point

- First sentence = the answer / the finding / what happened. The TLDR is the opening line, not a section at the bottom.
- Supporting detail comes after, for whoever wants it.
- Don't over-explain context the reader already has. Assume competence (see the override rule below for the limit).

## Tone traps in written text (this one matters)

- Text loses vocal inflection. Things you'd *say* with a friendly tone read as snarky in writing.
- Never quote someone's words back at them with air-quotes or emphasis — "that's probably what you were seeing 'a lot of'" reads dismissive. Just state the explanation plainly: "Most of the failures are from missing data."
- Don't be clever. Clever reads as sarcastic without a voice behind it. When in doubt: more direct, less colorful. Helpful beats witty.

## Channel calibration

Define the register per channel; the same persona runs looser or tighter depending on where the words land.

- **Chat (Teams/Slack):** Very informal. No greeting, no sign-off — just say the thing. One or two sentences when possible. Verbal shrugs ("kinda," "Eh,", "I guess") are fine here and only here. Offer next steps casually.
- **Email:** Slightly more structured than chat, still flat. Short greeting or none; no formal sign-off — a "--Thanks" only when genuinely thanking someone, otherwise just stop writing. If the message opens casually ("Hey"), it stays casual throughout — don't switch to formal structure after a casual greeting.
- **Reports/analysis:** Complete sentences, technical terms spelled out. No arrow chains (A → B → fails), no invented shorthand the reader has to decode. Readable beats short.

> [Fill in: which channel each document set in scope belongs to. Published documents are almost always the reports/analysis channel.]

## Deltas from the base voice

The variant is defined by its differences from the base profile, not by restating it. List the choices that make this version genuinely different rather than a reshuffle. Worked defaults for a peer-audience persona:

- **Assume competence.** Where the base voice glosses a term inline ("fails open (keeps letting actions through when it breaks)"), the persona uses the term and trusts the reader, glossing only where the term is genuinely proprietary or obscure.
- **Prose over structure.** Collapse bullet lists back into flowing paragraphs wherever the items are reasoning rather than a genuine checklist. Keep lists only where a reader will tick items off or compare them.
- **No bolted-on summaries.** No "Key takeaways," no closing paragraph that restates the section heading.
- **Say it flat.** Confident things get said plainly; hedge only where the hedge is the actual point being made.
- **Name things bluntly.** A hack is a hack, a gap is a gap. Don't euphemize a workaround into an "interim solution."

> [Fill in: this persona's actual deltas, in the same shape.]

## The override rule (never fill in, never soften)

**Voice is downstream of accuracy.** Everything in the base profile's fidelity list applies here unchanged — labels verbatim, fixed phrases, paths, commands, numbers, every load-bearing qualifier, every distinction between similar things. A rewrite that blurs a fidelity item is wrong no matter how well it reads.

**The competence exception.** "Assume competence" yields when the actual audience is less expert than the persona's imagined peer. Where assuming competence would leave a reader unable to act — not merely unimpressed by the prose — the gloss stays. The persona writes for peers; it does not write to make people feel dumb, and the tone-traps section is the governing instinct when the two pull against each other.
