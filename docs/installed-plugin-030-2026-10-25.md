# Local plugin 0.3.0 rollout

The 4070pc user installation was updated from 0.2.0 to 0.3.0 on October 25,
2026. This closes `tali:update-installed-plugin-030`.

## Installation

`claude plugin update tali@tali --scope user --json` completed successfully
and reported `oldVersion: 0.2.0`, `newVersion: 0.3.0` and `outcome: ok`.
The installed registry and plugin manifest both report 0.3.0. The registry
records source commit `76d3a131f4ad5f01685e70ac4ce151f5d9007c84`, which matched
the published `main` revision at verification time.

The user cache is `~/.claude/plugins/cache/tali/tali/0.3.0`.
A fresh `claude plugin details tali@tali` process resolves version 0.3.0 and
lists `voice-mutate`, `voice-review` and `voice-publish`. Already-running
Claude sessions require a restart to reload the updated plugin; they were
not interrupted during this rollout.

## Verification

All three installed skill files and
`skills/voice-mutate/references/audience-adaptation.md` match the published
Git source after newline normalization. The first raw-byte comparison found
the cache uses CRLF while the source checkout uses LF; normalized text and
Git object content agree, with no instruction differences.

- `voice-mutate` includes audience adaptation, explicit selective coverage,
  and its link to the audience procedure.
- `voice-review` includes audience editions with different depth and length,
  plus coverage-specific verification.
- `voice-publish` includes depth-tier purpose/length labels and summary
  navigation guidance.
- `python -m unittest discover -s <installed-plugin>/tests` ran all 71 tests
  successfully, without skips. Existing unclosed-file ResourceWarnings were
  emitted by build-tool tests and did not fail the suite.

The Dias chip now records the rollout as done. The status retains the previous
human percentage assessment rather than calculating a new score from chip
completion; its remaining-work text and milestone phase reflect this closeout.
No new writing campaign or remote-host installation is claimed by these checks.
