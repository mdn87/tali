# Marketplace installation evidence, 2026-10-23

The marketplace installation and shipped checks passed on a second host. A
subsequent real-document voice pass also passed; see the
[validation continuation](committee-brief-validation-2026-10-23.md). The owner
accepted the result and confirmed that Lugos-host never held a source clone
before installation. This step is done. The subsequent full second-campaign
round is documented in the [reuse evidence](second-campaign-validation-2026-10-23.md).

## Target and provenance

- Target: inventoried Lugos-host, Debian GNU/Linux 13, operator account.
- Claude Code: 2.1.302. Python: 3.13.5.
- Before installation, no Tali paths were found within five levels of the
  operator home or the service repository directory; the plugin list contained
  no Tali installation. The owner subsequently confirmed no prior source clone.
- Applemac was excluded because its MyDocs directory already contained Tali.
- Installed version: 0.2.0, commit
  `4358a29d6915317ae2ee8a9a27279cafa551ba9e`.

## Installation and checks

The public marketplace was added with `claude plugin marketplace add mdn87/tali`,
then installed with `claude plugin install tali@tali`. Both commands succeeded.
The CLI cloned the marketplace over HTTPS and enabled the plugin at user scope.
`claude plugin details tali@tali` listed `voice-mutate`, `voice-publish`, and
`voice-review`. This verified the installed component inventory. The subsequent
real-document invocation is recorded in the validation continuation.

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

The installation and verification each completed in seconds. During this initial
installation session, no campaign document, skeleton, or voice copy was created
or transferred. Raw installation,
package metadata, and check output are retained in the author's ignored
`.lugos-wip/install-outside-origin/` directory.

## Acceptance and closeout

The validation continuation supplies the real-document voice-pass evidence.
On 2026-10-23 the owner accepted the rewritten brief and confirmed that Lugos-host
never held a Tali source clone before the marketplace install. Both acceptance
requirements are now satisfied. The board marks this step done. The subsequent
second-campaign round was reopened for voice differentiation after owner review,
as recorded in the reuse evidence.
