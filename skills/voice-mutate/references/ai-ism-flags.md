# AI-ism Flags — De-tell Pass Reference

Purpose: the machine-tell patterns to strip during a voice pass, with the test for the one tell that sometimes has to stay.

`tools/check_tells.py` runs the mechanical half of this list: the strip-on-sight vocabulary, hedging stacks, and em-dash density fail the lint; negation-contrasts, rhetorical questions, and symmetrical endings are reported for a human to judge. This file is the source of truth for the vocabulary; when it changes, the script's list is updated to match.

## Strip on sight

- "It's worth noting," "importantly," "crucially," "essentially," "robust," "leverage," "seamless," "holistic," "comprehensive."
- Triplet lists used as rhythm filler ("clear, concise, and consistent"). Three items are fine when there are actually three things; a triad chosen for cadence is filler.
- Em-dash interjections more than once per page. Rewrite with commas, "so," or parentheses.
- Symmetrical paragraph endings that restate the heading ("...and that's why monitoring matters" at the end of a section titled "Why monitoring matters").
- Hedging stacks ("may potentially, in some cases"). One hedge, if any, and only when uncertainty is real.

## The negation-contrast tell (the big one)

The loudest machine tell is the **rhetorical negation-contrast**: raise a thing nobody claimed, deny it, then state the real point. It reads like padding because it is.

Problematic examples (the pattern to cut):

> "This isn't just a formatting tool. It's how the whole team keeps a consistent codebase."
> "Caching isn't a niche optimization. It's the difference between a usable app and a slow one."
> "That's normal behavior, not a malfunction."
> "A steady stream of alerts is the system working, not noise."

The fix: say the real point on its own.

> "The formatter is how the team keeps the codebase consistent."
> "Caching is the difference between a usable app and a slow one."
> "Expect that behavior — it's normal."
> "Expect a steady stream of alerts."

**But keep a negation when it does real work.** The test: would a reader actually believe the negated thing? If the negation corrects a live misconception or states a real limit or boundary, it stays, word for word:

- "reduces exposure but is **not** a sandbox" — states a real limit the reader would otherwise assume away.
- "the free tier is **not** covered by the support contract" — corrects an assumption of parity.
- "the examples are **not** production-ready" — a boundary the reader needs before acting.
- "a comment that says 'do not call this in a loop' is **not** an enforcement mechanism" — corrects a live misconception about what actually constrains behavior.
- "'Not supported' is a real answer" — corrects the assumption that every feature exists somewhere.

Rule of thumb: one earned negation per page is plenty. If the negated half is scaffolding for rhythm, cut it. If it's the actual limit or correction, keep it exactly — that kind of negation is usually on the fidelity list.

## Rhetorical-question transitions

Questions used as section glue ("So what does this mean for your team?", "Why does this matter?") are a tell. Replace with the answer stated directly. A question is only legitimate when the document genuinely goes on to weigh alternatives, not when it's a drum-roll for a point already decided.
