# Audience adaptation: selection, explanation and depth

Use this mode for requested summaries, nontechnical explanations, decision
briefs or expanded technical editions. Tone-only changes use the full-coverage
voice-mutate procedure. Tiers should help readers do different jobs; changing
synonyms or padding to a word count is insufficient.

## Establish the contract before drafting

Keep the original source and complete fact skeleton pinned. For each edition,
record the reader's task and assumed knowledge, then define:

- Coverage mode: selective summary, full coverage or expanded explanation.
- Approximate reading budget and length appropriate to the task.
- Essential claims, decisions, risks and qualifiers that must appear.
- Groups that may be condensed or deferred, why, and where the complete detail
  remains available. Identify summaries as summaries.
- Concepts needing definitions or explanation, and evidence supporting them.

For example, an overview might explain purpose, value, risks and decisions in
a few hundred words; a committee brief might add evidence and tradeoffs; a
technical edition might retain complete evidence and explain the mechanisms
and limitations. Choose scope from the actual request rather than imposing
fixed ratios. Respect novice readers without calling them unintelligent or
substituting childish language for clear explanation.

## Draft to the reader's needs

Change selection, structure, explanation and vocabulary together. Headings and
paragraph counts need not match across tiers. Keep ordered procedures and
priorities in order when presented. Do not present a selected subset as the
complete list. Full reference tables may live in the detailed edition rather
than every summary; any reproduced unchanged table remains a reference artifact.

Explain jargon through its function. Ground definitions and interpretation in
the supplied material or separately identified supporting sources. Distinguish
explanation from reported observations. Never invent implementation details,
assurances, results, recommendations or approvals. Proposed work stays proposed.

Every retained claim keeps the scope and conditions needed to interpret it.
Selection cannot turn partial success into overall success, a report into a
safety gate, permission into effectiveness, or a corrected defect into completed
validation. Do not omit a material counterexample or limitation that would
change the reader's decision.

## Verify the appropriate coverage

1. Map source claim groups to **retained**, **condensed** or **deferred** for each
   tier. Give deferral reasons and identify added explanations. Never change the
   original skeleton to fit the copy.
2. Check every assertion in the adaptation against the source, as well as
   essential coverage. This catches unsupported additions.
3. Give an independent verifier the source, full skeleton, tier contract and
   adaptation without writer reasoning. Check included assertions, essential
   coverage, qualifiers, misleading omissions and support for explanations.
   Resolve findings in the edition.
4. Run de-tell lint; document earned review findings.
5. Full-coverage editions still run the unchanged `check_fidelity.py` contract.
   That checker requires all configured source items in every configured copy;
   it is **not a summary validator**. Do not put selective summaries into the
   full-copy config, delete protected phrases or add blanket waivers for a pass.
   Report their separate semantic/coverage review honestly. Narrow literal
   checks may supplement it, but must be labeled with their limited scope.
6. Check audience utility separately: can a novice explain purpose and the main
   limitation, can a decision-maker identify the decisions, and does a technical
   reader gain supported understanding rather than a longer paraphrase? Inspect
   selection and explanation, not just word counts or readability scores.
   Report agent judgments as such; do not claim a human test that did not occur.

Record word counts, coverage decisions, validation scope, findings and artifact
refs together. A summary is complete when essential coverage and all included
assertions pass review, not when every source sentence reappears.
