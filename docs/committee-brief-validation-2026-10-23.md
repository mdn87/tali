# Real-document validation, 2026-10-23

The user supplied `IT-COMMITTEE-BRIEF.md` for the outstanding document pass.
The marketplace-installed Tali 0.2.0 plugin on Lugos-host produced a plain
professional version. Its mechanical checks passed, and an independent semantic
review found one wording correction, which was applied and checked.

The owner accepted the rewritten brief and confirmed on 2026-10-23 that
Lugos-host never held a Tali source clone before the marketplace installation.
That confirmation closes the remaining provenance requirement, and the board
step is done. The later full multi-voice campaign round is also complete; see
the [second-campaign evidence](second-campaign-validation-2026-10-23.md).

## Execution evidence

- Installed plugin commit: `4358a29d6915317ae2ee8a9a27279cafa551ba9e`.
- A fresh Claude Code session resolved all three installed Tali skills.
- The run invoked `tali:voice-mutate`, extracted and persisted the fact skeleton
  before drafting, then continued with the saved skeleton and voice profile.
- The source file's SHA-256 matched on the source machine and Lugos-host.
- The skeleton contained 95 claims and 21 distinctions. Before drafting, two
  distinction descriptions were corrected against the source to avoid stronger
  assertions. No mechanically protected phrases were removed.
- A source-baseline check passed all 147 declared and automatically extracted
  items before drafting. The first draft also passed all 147 items.
- Independent review checked every claim and distinction, the full enumerations,
  qualifier attachment, limitations, and requests. It found one unsupported
  causal connector. Removing that connector was the sole post-review prose edit.
- Final installed-tool results: `PASS: 1/1 voice copies carry every fidelity
  item` (147 items, exit 0); `PASS: 0 strip, 3 review` (exit 0).
- All three review findings retained protected source wording and received
  written dispositions. No waivers were added.
- The metrics table remained byte-identical. Source, skeleton, voice-profile,
  and fidelity-config hashes remained unchanged through the rewrite and fix.
- The final copy is longer than the source: 1,417 versus 1,306 whitespace-delimited
  words. This validates plain-language rewriting, not a reduction in length.

The skeleton extraction took approximately 79 seconds. Drafting time was not
recorded separately from resumed-session and completion-hook processing. The
two phases were separated by source review, persistence, and validation.
The CLI's final result field held a completion-hook reply, so the wrapper
recovered the single complete document from the assistant event stream. No
permission denial occurred and no generation retry was needed.

## Artifact handling

The campaign source, skeleton, rewritten copy, checks, and semantic review remain
in private working artifacts, outside the public repository history. The user
received a local plain-language copy and validation record alongside the source.
Only this evidence summary and board state are published. Detailed artifacts are
retained on Lugos-host and in the source machine's ignored working directory.

The source SHA-256 was
`f1bfa9fcbff43a20b8508af3a6310634c5d0cf0747c4056b5ec6850896033d71`;
the final copy SHA-256 was
`d75479d38d094bc565ae7c3796bf80e3a1db1dc1cc88d8a28f5684e66f1fbb60`.
