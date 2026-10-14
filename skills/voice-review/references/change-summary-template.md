# Change Summary per Voice — Template

Purpose: what a reviewer needs to know about one voice pass before reading it: what moved, what was compressed, what the verifier flagged, and how each flag was resolved. One file per voice per round, next to the round record.

```markdown
# Change summary: [voice key] — round [N]

Voice spec: [path] at [commit hash]
Source ref: [original pin hash]
Voice ref: [branch or directory] at [commit hash]

## Size
| File | Source words | Voice words | Change |
|---|---|---|---|
| [file] | [n] | [n] | [-x%] |
| Total | [n] | [n] | [-x%] |

## What moved
- [file]: [structural change: a list collapsed into prose, a section reordered, a table left as-is]

## What was compressed
- [file]: [what got shorter and what carried it: "the three-paragraph rationale is now one paragraph; the qualifier Q1 stays attached to the first sentence"]

## What stayed verbatim
- Everything in the skeleton's Verbatim, Labels, Fixed phrases, and Qualifiers sections. Fidelity check: [PASS, exit 0, date].

## Verifier flags and resolutions
| Flag | File | Item | What the verifier saw | Resolution |
|---|---|---|---|---|
| [F1] | [file] | [Q2] | [qualifier read as unconditional] | [restored in sentence 3; re-verified] |

## Waivers in force
- [item, document, reason] or none

## De-tell pass
- Strip findings: [n], all resolved. Review findings kept: [n], each an earned negation or a genuine alternatives question.

## Known limits of this voice
- [where the voice had to stay closer to the source than the spec would like, and why: usually a fidelity item that would not compress]
```
