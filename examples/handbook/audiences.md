# Audiences — Team tools handbook

Instantiated from `skills/voice-review/references/audience-template.md`.

---

## Audience: New hires

**Who they are.** People in their first month, any role, who have to use the sync agent and one of the two client programs without having seen either before.

**What they need from these documents.** To get set up without asking anyone, and to know the data-handling boundary before their first upload.

**What they already know.** General software literacy: cloning a repository, running a command, editing a config file. Not the team's vocabulary.

**What they are likely to misread.** That the CLI and the desktop app share settings (they do not). That "synthetic" or "public" alone satisfies the policy (it does not; the boundary is the full phrase). That the agent protects them from uploading the wrong thing (it reduces exposure but is not a sandbox).

**Voice that serves them.** `voice-profile.md` in this directory (the plain voice). Voice copies live under `voices/plain/`.

**Channel.** Published handbook (site and PDF).

**Acceptance test.** A new hire completes the setup checklist and states the data-handling boundary in the policy's own words, without opening a second document.

**Out of scope for this audience.** Nothing; new hires read every document.

---

## Audience: Engineers

**Who they are.** People who already run the tools and need the reference wording when they open or triage a request.

**What they need from these documents.** The exact tier definitions, the exact policy boundary, the exact commands.

**What they already know.** Everything the documents gloss.

**What they are likely to misread.** Nothing the plain voice would fix; this audience reads the original prose.

**Voice that serves them.** The original prose, pinned in the site config as the `orig` version.

**Channel.** Published handbook.

**Acceptance test.** An engineer can quote a tier's response window from the overview without re-reading the paragraph around it.

**Out of scope for this audience.** Nothing.

---

## Coverage check

| Document | New hires | Engineers |
|---|---|---|
| overview.md | plain | original |
| guides/setup.md | plain | original |
| policy/data-handling.md | plain | original |
