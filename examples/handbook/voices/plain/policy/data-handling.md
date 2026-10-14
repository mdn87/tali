# Data-handling policy
**Status:** example

This policy says what you can send to the hosted service and what has to stay on the local install.

## What goes to the hosted service

Only public or fully synthetic data goes into the hosted service. Customer data, internal documents, and anything under a non-disclosure agreement stay on the local install.

**Ask first.** If you're not sure whether a dataset counts as public or fully synthetic data, ask the platform team before you upload it. Open a Tier 3 request for that.

## What the sync agent does and does not do

The sync agent reduces exposure but is not a sandbox. It strips file metadata and blocks uploads larger than 50 MB, and it does nothing to inspect the content of a file. You're responsible for what you upload.

## Retention

The hosted service keeps uploaded files for 30 days and then deletes them. The local install keeps files until you delete them yourself. The two don't talk to each other: deleting a file locally does not delete the hosted copy, and the hosted copy expiring does not touch the local file.

## Reference

| Setting | Hosted service | Local install |
|---|---|---|
| Allowed data | public or fully synthetic data | any |
| Size limit | 50 MB per file | none |
| Retention | 30 days | until deleted |
| Content inspection | none | none |
