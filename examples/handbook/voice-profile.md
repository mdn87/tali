# Base Voice Profile — Team tools handbook, plain voice

Instantiated from `skills/voice-mutate/references/voice-profile-template.md`. The template's defaults apply wherever this file does not override them.

**This is a style spec, not a content license.** The fidelity list at the bottom always wins: lower reading complexity, never lower conceptual precision.

## The voice in one paragraph

Talk to a new hire the way a helpful teammate would on their second day: lead with what to do, say why in the same sentence, and name the tool you mean. Explain a term the first time it appears through what it does. Be direct about limits without making them sound alarming.

## Register: published, not chat

Calibration test: would this read naturally as an onboarding email from the platform team to every new hire? Contractions yes; verbal shrugs no. The reader is "you"; the platform team is "the platform team", never "we", because the reader is not on it yet.

## Overrides of the template defaults

- Keep the status chips (`**Status:**`, `**Owner:**`) exactly as they are; the publish config drops them from the page.
- Checklists stay checklists. They are the one place a bullet beats prose for this audience.
- Tables are reference material and are never voice-passed.

## Fidelity list (MANDATORY)

The mechanical half of this list lives in `tali.fidelity.json` and the per-document skeletons under `skeletons/`; `tools/check_fidelity.py` enforces it. The items are repeated here so the spec is readable on its own.

- **Labels and taxonomies, verbatim.** The three support tiers are named `Tier 1`, `Tier 2`, `Tier 3`, in that form, and there are exactly three. Never "first tier", "P1", or "critical".
- **Paths, commands, code, product names, and numbers.** `npm ci`, `npm install`, `tali-agent --port 8080`, `tali-agent --check`, `~/.tali/config.toml`, `Node.js 22`, `50 MB`, `30 days`, the three response windows in business days, and the port `8080`.
- **Fixed phrases with defined meaning.** `public or fully synthetic data` is the policy boundary. "Public data", "synthetic data", or "public-ish data" each claim something different.
- **Load-bearing qualifiers.** `only when the sync service is running`; `reduces exposure but is not a sandbox`; `does nothing to inspect the content of a file`; `exactly one of three support tiers`; `once triage has looked at it`; `deleting a file locally does not delete the hosted copy`. The instruction not to run `npm install` is a claim (C2 in the setup skeleton): the wording is free to loosen, the meaning is not.
- **Distinctions between similar things.** The CLI versus the desktop app (separate programs, separate settings; only the CLI reads the config file). The hosted service versus the local install (different allowed data, size limit, and retention). The triager versus the opener of a request (only the triager sets the tier).
