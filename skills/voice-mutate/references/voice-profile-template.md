# Base Voice Profile — Template

Purpose: a fill-in template for defining the BASE VOICE of a document set. The rules below are a worked default (plain professional voice, one register up from chat); replace the bracketed slots to specialize it, keep the rules you don't override.

**This is a style spec, not a content license.** The fidelity list at the bottom always wins: lower reading complexity, never lower conceptual precision.

## The voice in one paragraph

> [Fill in: one paragraph describing how the writer talks to the reader.]

Default: talk to the reader like a sharp colleague you respect but who doesn't live in this world. Lead with the point. Explain a term the moment you use it, through what it does for you, not what category it belongs to. Say why in the same breath as what. Be direct about risk without being dramatic about it. If a sentence would make someone feel dumb for having to reread it, rewrite it.

## Sentence shape

- Lead with the point, then the reason. Not the reverse.
- Prefer one flowing sentence joined with "so," "and," or "because" over two stiff ones joined by a semicolon. Semicolons are almost always a rewrite flag.
- Kill em-dash chains. Use commas, "so," or parentheses (sparingly). One dash pair per page is plenty.
- Vary length. Short sentence to land a point. Longer one to explain it.

## Word choice

- Contractions are normal: don't, it's, you'll, that's.
- The reader is "you." The organization is "we." Tools and products are called by name.
- Plain verbs over inflated ones:

  | Instead of | Write |
  |---|---|
  | utilize | use |
  | provision | set up |
  | validate | check |
  | retain | keep (unless the formal phrase is a fixed term of art, e.g. "data retention") |
  | facilitate | help / let |
  | leverage | use |

- No bureaucratic noun stacks: "the review process for equipment loan requests" becomes "how an equipment loan gets approved."
- Explain jargon inline on first use in each document, by function, not by category: "a lockfile (the file that records exactly which versions got installed)" — not "a lockfile (a dependency-management artifact)."

## Tone

- Direct beats hedged. "This will happen" when it will; "this can happen" only when it genuinely might not.
- Honest about limits without theater. The model sentence shape: "these controls reduce risk, they are not a guarantee." State the limit plainly and move on — no drama, no reassurance padding.
- A light touch of dry humor is fine where it aids memory. Never jokey about risk consequences.
- No throat-clearing openers ("It is important to note that..."). Just say it.

## Structure

- Short paragraphs, 1-4 sentences.
- Bullets only for genuinely parallel items; prose for reasoning. Don't bullet a thought that needs connective logic.
- Headings stay short and plain.

## Register: published, not chat

The default calibration target is one notch up from the author's chat voice: keep the directness and plain verbs, publish at professional-email level.

- Contractions yes; verbal shrugs no ("kind of," "basically," "pretty much," "a bunch of," "stuff").
- Address the reader as "you," but don't chat at them ("here's the thing," "the funny part is," "look,").
- Confident statements, not asides. If a sentence would work as a spoken aside and nothing else, cut it.
- No rhetorical questions used as transitions.
- Full sentences and capitalization; drop shorthand and profanity even if the source corpus has them.

The calibration test: **would this read naturally as an email from the author to the whole office?** If it's stiffer than that, loosen it. If it's chattier than that, tighten it.

> [Fill in: if this document set targets a different register (internal wiki, public docs, exec brief), restate the test for that audience.]

## Fidelity list (MANDATORY — fill this in before any voice pass)

Enumerate what survives every rewrite exactly. A voice pass that touches an item on this list is wrong no matter how well it reads. Cover at least these categories:

- **Labels and taxonomies, verbatim.** Any fixed set of named categories the document set defines (status labels, severity tiers, classification names). Example: if the set defines exactly four incident severities named "Sev-1" through "Sev-4," those names never get paraphrased into "critical/major/minor" and the set never gains or loses a member.
- **Paths, commands, code, config, product names, and numbers.** Copied exactly, character for character. "Run `npm ci` in the repo root" doesn't become "install the dependencies."
- **Fixed phrases with defined meaning.** Any phrase the document set treats as a term of art (a data-handling formula, a scope statement, a legal-ish clause). If "public or fully synthetic data" is the defined boundary, "public-ish data" is a fidelity break.
- **Load-bearing qualifiers.** Every conditional or scope-limiting clause that carries real meaning: "when the sync service is running," "reduces exposure but is not a sandbox," "vendor-documented, not independently tested." Simplifying the sentence is fine; dropping the condition is not.
- **Distinctions between similar things.** Pairs the reader could plausibly conflate (the CLI vs the desktop app; read access vs write access; the hosted service vs the local install). If the rewrite blurs a distinction the source keeps sharp, the rewrite is wrong.

> [Fill in: the concrete items for this document set, one bullet each. Be exhaustive — the verification pass checks against this list.]
