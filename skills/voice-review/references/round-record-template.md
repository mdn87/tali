# Round Record — Template

Purpose: the record of one multi-voice round, kept so the next round starts from facts instead of memory. One file per round, committed with the round's output. Keep every path repo-relative and every ref a full hash or a branch name.

```markdown
# Round [N]: [document set] — [YYYY-MM-DD]

## Scope split
- Voice-passed: [list of files, or a glob plus exclusions]
- Reference (never voice-passed): [files]
- Generated (rebuilt, never hand-edited): [files]

## Refs compared
- Original pin: [commit hash] (committed [date], before the first pass)
- [voice key]: [branch name or directory] at [commit hash]
- [voice key]: ...

## Voice specs used
- Base voice: [path] at [commit hash]
- [voice key]: [persona guide path] at [commit hash] (seeded from masq profile [id], if any)
- Fidelity list: [tali.fidelity.json path] at [commit hash]; skeletons under [skeletons_dir]

## Passes run
| Voice | Files | Run by | Date | Notes |
|---|---|---|---|---|
| [key] | [n] | [agent/person] | [date] | [parallelism, retries] |

## Fidelity check
- Command: `python tools/check_fidelity.py --config [path]`
- Result: [PASS/FAIL], [n]/[m] voice copies, exit [code], on [date]
- Waivers added this round: [item, voice, document, reason] or none

## De-tell lint
- Command: `python tools/check_tells.py [paths]`
- Result: [n] strip, [m] review; strip findings resolved: [how]; review findings kept as earned: [ids or count]

## Verifier findings
| ID | Voice | File | Skeleton item | Finding | Resolution |
|---|---|---|---|---|---|
| F1 | [key] | [file] | [Q2] | [what drifted] | [fixed in copy / waived: reason] |

## Artifacts produced
- Comparison site: [site_dir] built from [config] on [date]
- PDF manuals: [files and labels]
- Change summaries: [paths]

## Open items carried forward
- [item, owner, why it is open]

## Decisions
- [decision, who made it, date] (voice-rule changes go to the spec; fact corrections go to the source)
```

A round is closed when the fidelity check exits 0 for every voice, the verifier findings table has no unresolved rows, and the artifacts are built from the refs listed above.
