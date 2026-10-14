# Redline Intake — Template

Purpose: classify every piece of marked-up feedback before touching anything, so a fact correction never lands in a voice copy and a phrasing nit never triggers a full re-run. One file per intake batch, next to the round record.

## Classification rules

| Class | Where it is fixed | What re-runs |
|---|---|---|
| **Fact correction** | the source prose only | every voice pass for the affected file, then the fidelity check |
| **Voice-rule change** | the voice spec (profile or persona guide) | that voice's pass for every file, then the fidelity check |
| **One-off phrasing** | the voice copy, only if the passage touches nothing on the fidelity list | the fidelity check for that voice |
| **Fidelity break** | the voice copy (restore the item) | the fidelity check; add the item to the skeleton if it was missing there |
| **Declined** | nothing | nothing; the reason is recorded |

A redline that asks for a change to a fidelity item (a label, a qualifier, a number) is a fact correction by definition, whichever copy it was marked on.

## Intake table

```markdown
# Redline intake: round [N], batch [B] — [date]

Source of feedback: [reviewer or group], marked on [voice key / original / PDF label]

| ID | File | Marked on | Feedback (quoted) | Class | Action | Re-run | Check |
|---|---|---|---|---|---|---|---|
| R1 | [file] | [voice] | "[quote]" | fact correction | [edit in source at commit] | [voices re-run] | [PASS/FAIL, date] |
| R2 | [file] | [voice] | "[quote]" | voice-rule change | [spec change at commit] | [voice re-run] | |
| R3 | [file] | [voice] | "[quote]" | one-off phrasing | [edited in copy] | none | |
| R4 | [file] | [voice] | "[quote]" | declined | — | none | [reason] |

## Totals
- Fact corrections: [n] (source changed: [yes/no], passes re-run: [voices])
- Voice-rule changes: [n] (specs changed: [paths])
- One-off phrasings: [n]
- Fidelity breaks: [n] (skeleton updated: [yes/no])
- Declined: [n]
```

Intake is closed when every row has a class, every non-declined row has an action, and the fidelity check exits 0 after the last re-run.
