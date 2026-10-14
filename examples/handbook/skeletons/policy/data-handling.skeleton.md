# Fact skeleton: policy/data-handling.md

## Claims
- C1: Customer data, internal documents, and NDA material stay on the local install.
- C2: The agent strips metadata and blocks files over 50 MB, and does not inspect content.
- C3: The uploader is responsible for content.
- C4: Hosted retention is 30 days; local retention is until the user deletes.
- C5: The two retention periods are independent in both directions.

## Verbatim
- V1: 50 MB
- V2: 30 days

## Labels
- L1: Tier 3

## Fixed phrases
- F1: public or fully synthetic data

## Qualifiers
- Q1: reduces exposure but is not a sandbox
- Q2: does nothing to inspect the content of a file
- Q3: deleting a file locally does not delete the hosted copy

## Distinctions
- D1: hosted service vs local install (different allowed data, size limit, and retention)
