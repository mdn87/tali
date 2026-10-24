# Marketplace installation evidence, 2026-10-23

The marketplace installation and shipped checks passed on a second host. The
step remains blocked: the host's prior clone history is not confirmed, and no
document from another campaign has been selected for the required voice pass.
The full second-campaign round was not started.

## Target and provenance

- Target: inventoried Lugos-host, Debian GNU/Linux 13, operator account.
- Claude Code: 2.1.302. Python: 3.13.5.
- Before installation, no Tali paths were found within five levels of the
  operator home or the service repository directory; the plugin list contained
  no Tali installation. This establishes observed absence, not historical absence.
- Applemac was excluded because its MyDocs directory already contained Tali.
- Installed version: 0.2.0, commit
  `4358a29d6915317ae2ee8a9a27279cafa551ba9e`.

## Installation and checks

The public marketplace was added with `claude plugin marketplace add mdn87/tali`,
then installed with `claude plugin install tali@tali`. Both commands succeeded.
The CLI cloned the marketplace over HTTPS and enabled the plugin at user scope.
`claude plugin details tali@tali` listed `voice-mutate`, `voice-publish`, and
`voice-review`. This verifies the installed component inventory; a voice-mutate
invocation on a real document has not yet been demonstrated.

The checks ran directly from the installed plugin package, without a separate
source checkout. Actual output:

```text
Ran 71 tests in 0.316s
OK (skipped=1)
PASS plain/guides/setup.md (14 items)
PASS plain/overview.md (11 items)
PASS plain/policy/data-handling.md (10 items)
PASS: 3/3 voice copies carry every fidelity item
PASS: 0 strip, 1 review
index.html                              18,133 bytes
plain.html                              17,041 bytes
```

The example's review finding was its existing, load-bearing distinction between
the person who triages a request and the person who opens it. The PDF test
skipped because the host has no headless browser. Python also reported unclosed
file ResourceWarnings in the existing build-tool tests and page builder; they
did not fail the suite. An extra diagnostic initially used a nonexistent test
class; the corrected targeted invocation confirmed the browser-related skip.

The installation and verification each completed in seconds. No campaign
document, skeleton, or voice copy was created or transferred. Raw installation,
package metadata, and check output are retained in the author's ignored
`.lugos-wip/install-outside-origin/` directory.

## Remaining acceptance evidence

Confirm that Lugos-host never held a Tali source clone, or identify another
qualifying machine. Select one real document from another campaign on that
machine. Run the installed voice-mutate skill, retain the source, skeleton, and
voice copy there, and record fidelity and de-tell results plus any corrections.
Keep this chip as the next step until that evidence exists.
