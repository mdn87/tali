# Data-handling policy
**Status:** example

This policy defines what may be sent to the hosted service and what stays on the local install.

## What goes to the hosted service

Only public or fully synthetic data goes into the hosted service. Customer data, internal documents, and anything under a non-disclosure agreement stay on the local install.

**Ask first.** If you are unsure whether a dataset counts as public or fully synthetic data, ask the platform team before uploading. A Tier 3 request is the right channel for that question.

## What the sync agent does and does not do

The sync agent reduces exposure but is not a sandbox. It strips file metadata and blocks uploads larger than 50 MB, and it does nothing to inspect the content of a file. The person uploading is responsible for the content.

## Retention

The hosted service keeps uploaded files for 30 days, then deletes them. The local install keeps files until you delete them yourself. These two retention periods are independent: deleting a file locally does not delete the hosted copy, and the hosted copy expiring does not touch the local file.

## Reference

| Setting | Hosted service | Local install |
|---|---|---|
| Allowed data | public or fully synthetic data | any |
| Size limit | 50 MB per file | none |
| Retention | 30 days | until deleted |
| Content inspection | none | none |
