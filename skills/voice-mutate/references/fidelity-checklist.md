# Fidelity Verification — Procedure

Purpose: the verification procedure that keeps a voice rewrite from silently changing what a document says.

## 1. Build the fact skeleton BEFORE rewriting

Before touching the prose, extract every load-bearing element of the source into a flat list:

- Every claim (what the document asserts is true).
- Every number, path, command, code snippet, and product name.
- Every label from a fixed taxonomy, verbatim.
- Every qualifier that limits scope or conditions a claim ("when the sync service is running," "not independently tested").
- Every distinction between similar things the source keeps sharp (CLI vs desktop app, read vs write, hosted vs local).

The skeleton is the contract. It's built from the source, once, before any rewriting — never reverse-engineered from the rewrite.

## 2. Per-file pipeline

Run each file through, in order:

1. **Fact skeleton** — extract as above.
2. **Compression + voice rewrite** — apply the voice profile (and persona deltas, if any). Compress freely; this is where sentences get shorter and structure gets flattened.
3. **Self-check against the skeleton** — the rewriter walks the skeleton item by item and points to where each item survives in the rewrite. Any item without a location is a break.
4. **Independent cross-verification** — a second pass or a separate agent, given the skeleton and the rewrite (not the rewriter's reasoning), repeats the walk. Fresh eyes catch drift the rewriter rationalized.

## 3. Cross-verification checklist

The second pass checks specifically for:

- **No permission-vs-effectiveness drift.** A statement about what's *allowed* must not become a statement about what's *safe* (or vice versa). "You may run this locally" and "this is safe to run locally" are different claims; so are "the tool blocks this" and "you shouldn't do this." Drift between allowed / safe / effective / recommended is the most common silent break.
- **No dropped enumerations.** If the source lists five conditions, the rewrite has five conditions. Compressing the wording is fine; losing a member is not.
- **No opened closed-lists.** "These three cases" must not become "cases like these." A closed list that becomes exemplary ("such as," "including," "e.g.") now claims less than the source — or more, depending on direction — and either way it's a break.
- **Qualifiers intact.** Every scope-limiting clause from the skeleton is still attached to its claim. A qualifier moved so far from its claim that the claim reads unconditional counts as dropped.
- **Distinctions intact.** Every pair the source distinguishes is still distinguishable in the rewrite. If both members now read as the same thing, the rewrite is wrong even if each sentence is individually accurate.

## 4. The rerunnable check

The verbatim half of this procedure is mechanical, so it runs as a script instead of a judgment call: `tools/check_fidelity.py`, driven by a `tali.fidelity.json` beside the document set (see `tools/tali.fidelity.example.json`). For every source document and every voice it requires each fenced code block, inline code span, URL, and number from the source, plus every phrase on the fidelity list the source contains, and prints PASS or FAIL per voice copy. Exit status 0 means every copy passed, 1 means at least one break, 2 means the config is wrong (including a fidelity phrase the source no longer contains).

Put labels, taxonomy members, fixed phrases, load-bearing qualifiers, and the wording that keeps a distinction sharp on the fidelity list as verbatim phrases; that is what makes them checkable. A pass is required before a voice pass is declared complete, and it is rerun after every fix and every redline.

What the script cannot judge is meaning drift in paraphrased prose: permission-vs-effectiveness drift, a qualifier still present but moved off its claim, a closed list reopened with "such as." Those stay with the cross-verification in section 3. A clean script run is necessary, not sufficient.

## 5. Failure handling

A fidelity break is fixed in the rewrite, never patched by weakening the skeleton. If the rewrite can't carry an item gracefully, the prose bends — restore the qualifier, re-close the list, re-split the blurred distinction — and the voice pass re-runs on that passage. The same goes for the script: a break is fixed in the voice copy or recorded as a waiver with a reason, never cleared by deleting the phrase from the fidelity list. Editing the skeleton to make the check pass defeats the entire procedure; the skeleton only changes if it misread the source, and that's verified against the source, not against the rewrite.
