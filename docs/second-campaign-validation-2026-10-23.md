# Second-campaign review round, 2026-10-23

Tali completed a full three-voice review and publication round on one real
document from a different campaign. The owner requested this round after
accepting the plain rewrite and closing the clean-machine installation proof.
The accepted plain copy was reused; decisions and technical voices were newly
written and independently reviewed. This proves reuse on a second campaign at
one-document scope, not a repetition of the original 26-document scale.

## Results

- All three voice copies passed all 147 mechanical fidelity items, exit 0.
- Independent reviewers checked 95 claims and 21 distinctions. One new scope
  correction was required and independently rechecked. No unresolved findings
  or fidelity waivers remain.
- The source, frozen skeleton and accepted plain copy retained their hashes.
  The title, seven section headings and metrics table remained identical.
- De-tell lint reported zero strip findings and eight review findings. Each
  review finding retained a source distinction and has a written disposition.
- The comparison contains the original and three voices. Browser checks passed
  for section-preserving voice switches, tables, desktop layout and mobile
  width; no JavaScript errors were reported.
- Four six-page PDFs were built, numbered, rendered and visually inspected.
  Extracted text from each final PDF passed the same 147 fidelity items.
- Audience definitions, profiles, per-voice change summaries, source-to-voice
  redlines, an empty human-feedback intake, a round record and artifact hashes
  are retained with the private campaign. New owner feedback was not invented;
  owner acceptance is recorded only for the previously accepted plain copy.

The local marketplace-installed Tali 0.2.0 tools were used. Its metadata pointed
to an earlier plugin commit, but all seven Python tools matched the validated
repository after line-ending normalization. No product-code change was needed.
A private PDF wrapper used the installed rendering helpers with print-break
rules and page footers. It also kept a protected compound on one line so
extracted PDF text could be checked without a waiver.

## Effort comparison

The owner recalled roughly **30 minutes of hands-on work** for the original
26-document, three-voice campaign. This is approximate; its automated elapsed
time is unavailable.

This round took **14.6 minutes of elapsed agent work to the review-package
checkpoint**, covering one document, two new voices and one reused accepted
voice. Final board and handoff bookkeeping followed that checkpoint. The prior
installation proof, source skeleton extraction and plain rewrite are excluded.
Current owner hands-on time was not measured. The timing measures and scopes
differ, so these observations do not establish a speedup.

## Reproducibility and closeout

The private campaign's source baseline is
`f1789cfe8887bf605a37225ff3bbb2259a340cbc`. Final voice and publication artifacts
are recorded at `6879d548381f092d9bafac54b4c9d4f9672eee12`; the subsequent round
record pins those refs and includes checks, reviewer dispositions and hashes.
The private repository has no remote. Campaign source and generated content
remain outside the public Tali history; only this evidence and board metadata
are published.

All seven current milestone steps are complete. Future human feedback can
start another revision, but no unresolved fidelity finding or missing artifact
remains in this round.
