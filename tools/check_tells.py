#!/usr/bin/env python3
"""Flag machine tells in markdown prose so the de-tell pass has a pass or fail output.

This mirrors skills/voice-mutate/references/ai-ism-flags.md. The "strip on
sight" list there is the source of truth for the vocabulary below; when
either file changes, check the other. Two severities:

- strip: the catalogue says cut on sight. Vocabulary hits, hedging stacks
  (two or more hedges in one sentence), and more than one em dash per page.
- review: a pattern that needs a human to decide whether it does real work.
  Negation-contrast candidates, rhetorical-question transitions, and a
  section whose last sentence restates its heading. An earned negation (a
  real limit or a corrected misconception) stays word for word, so these
  never fail a run unless --strict is given.

Fenced code blocks, inline code spans, markdown link targets, and YAML
frontmatter are removed before matching. Blockquotes are prose and stay in.
Line numbers refer to the original file.

Usage:
    python check_tells.py PATH [PATH ...]            # .md files or directories
    python check_tells.py docs/ --strict             # review findings also fail
    python check_tells.py doc.md --allow comprehensive --allow robust
    python check_tells.py doc.md --json
    python check_tells.py doc.md --page-words 300    # em-dash allowance per N words

Exit status: 0 no strip findings; 1 at least one strip finding, or any review
finding with --strict; 2 bad arguments or an unreadable path.
"""

import argparse
import bisect
import json
import math
import os
import re
import sys

DEFAULT_PAGE_WORDS = 400
SKIP_DIRS = {"node_modules", "site"}

# (allow key, forms). "--allow KEY", or any form, silences the whole group.
VOCABULARY = [
    ("it's worth noting", ("it's worth noting", "it is worth noting")),
    ("importantly", ("importantly",)),
    ("crucially", ("crucially",)),
    ("essentially", ("essentially",)),
    ("robust", ("robust",)),
    ("leverage", ("leverage", "leverages", "leveraged", "leveraging")),
    ("seamless", ("seamless", "seamlessly")),
    ("holistic", ("holistic",)),
    ("comprehensive", ("comprehensive",)),
]

HEDGES = ("may", "might", "could", "potentially", "possibly", "perhaps",
          "in some cases", "to some extent", "arguably", "it seems", "likely")

QUESTION_OPENERS = ("so what", "why does", "what does this mean", "but why")

APOS = "['’]"


class UsageError(Exception):
    pass


def term_re(term):
    """Whole-word, case-insensitive; straight or curly apostrophes."""
    words = [re.escape(w).replace("'", APOS) for w in term.split()]
    return re.compile(r"(?<![\w-])" + r"\s+".join(words) + r"(?![\w-])", re.I)


VOCAB_RES = [(key, [term_re(f) for f in forms]) for key, forms in VOCABULARY]
HEDGE_RES = [(h, term_re(h)) for h in HEDGES]

NEGATION_RES = [re.compile(p, re.I) for p in (
    rf"\bisn{APOS}t just\b",
    r"\bis not just\b",
    rf"\baren{APOS}t just\b",
    r"\bare not just\b",
    rf"\bnot just\b.*\bit{APOS}s\b",
    rf"\bisn{APOS}t about\b",
    r"\bis not about\b",
    r"\bnot only\b.*\bbut\b",
    r",\s*(?:not|no)\s+[^,;]+[.!]?\s*$",       # <clause>, not <clause>.
    rf"^(?:this isn{APOS}t|that{APOS}s not|it{APOS}s not|these aren{APOS}t)\b",
)]

# The em dash itself, or ASCII "--" used as one (word--word, word -- word).
# Flags such as --strict and rule lines such as --- are not counted.
EM_DASH_RE = re.compile(r"—|(?<=\w)--(?=\w)|(?<=\w )--(?= \w)")
WORD_RE = re.compile(r"[A-Za-z0-9]+(?:['’][A-Za-z]+)?")

FENCE_RE = re.compile(r"^ {0,3}(```|~~~)")
INLINE_CODE_RE = re.compile(r"(`+)[^`\n]+?\1")
LINK_TARGET_RE = re.compile(r"\]\([^)\n]*\)")
HEADING_RE = re.compile(r"^ {0,3}(#{1,6})[ \t]+(.*?)[ \t]*#*[ \t]*$")
LIST_MARKER_RE = re.compile(r"^[ \t]*(?:[-*+]|\d+[.)])[ \t]+")
RULE_LINE_RE = re.compile(r"^[ \t]*(?:[-*_][ \t]*){3,}$")
BOUNDARY_RE = re.compile(
    r"[.!?][\"'’”)\]]*(?=\s+[\"'“(\[A-Z0-9])"   # end punctuation, then a new sentence
    r"|[.!?][\"'’”)\]]*\s*$"                     # end of the block
    r"|\n(?=[ \t]*(?:[-*+]|\d+[.)])[ \t])"        # next list item
)


def clean(raw):
    """Prose only, every line kept in place so offsets still map to lines."""
    lines = raw.replace("\r\n", "\n").split("\n")
    out = list(lines)
    body_start = 0
    if lines and lines[0].strip() == "---":
        for j in range(1, len(lines)):
            if lines[j].strip() in ("---", "..."):
                for k in range(j + 1):
                    out[k] = ""
                body_start = j + 1
                break
    fence = None
    for j in range(body_start, len(lines)):
        m = FENCE_RE.match(lines[j])
        if fence is None:
            if m:
                fence = m.group(1)
                out[j] = ""
        else:
            out[j] = ""
            if m and m.group(1) == fence:
                fence = None
    text = "\n".join(out)
    text = INLINE_CODE_RE.sub(" ", text)
    return LINK_TARGET_RE.sub("]", text)


class Doc:
    def __init__(self, path, raw):
        self.path = path
        self.text = clean(raw)
        self.starts = [0] + [m.end() for m in re.finditer(r"\n", self.text)]

    def line(self, offset):
        return bisect.bisect_right(self.starts, offset)


def blocks(doc):
    """(kind, start, end) for each run of non-blank lines; headings stand alone."""
    out = []
    cur = None
    pos = 0
    prev_end = 0
    for line in doc.text.split("\n"):
        end = pos + len(line)
        if not line.strip():
            if cur is not None:
                out.append(("prose", cur, prev_end))
                cur = None
        elif HEADING_RE.match(line):
            if cur is not None:
                out.append(("prose", cur, prev_end))
                cur = None
            out.append(("heading", pos, end))
        elif cur is None:
            cur = pos
        prev_end = end
        pos = end + 1
    if cur is not None:
        out.append(("prose", cur, prev_end))
    result = []
    for kind, start, end in out:
        first = doc.text[start:end].split("\n", 1)[0]
        if kind == "prose" and first.lstrip().startswith("|"):
            kind = "table"
        elif kind == "prose" and RULE_LINE_RE.match(first):
            kind = "rule"
        result.append((kind, start, end))
    return result


def norm(s):
    s = re.sub(r"(?m)^[ \t]*>[ \t]?", "", s)
    s = LIST_MARKER_RE.sub("", s)
    return " ".join(s.split()).strip(" *_")


def plain(s):
    return re.sub(r"[*_`]", "", s).lower()


def sentences(doc, start, end):
    """(normalized sentence, offset in doc.text) for a prose block."""
    text = doc.text[start:end]
    pos = 0
    pieces = []
    for m in BOUNDARY_RE.finditer(text):
        pieces.append((pos, m.end()))
        pos = m.end()
    if pos < len(text):
        pieces.append((pos, len(text)))
    for a, b in pieces:
        raw = text[a:b]
        s = norm(raw)
        if s:
            yield s, start + a + (len(raw) - len(raw.lstrip()))


def short(s, width=120):
    return s if len(s) <= width else s[: width - 1] + "…"


def finding(doc, offset, severity, rule, detail):
    return {"path": doc.path, "line": doc.line(offset), "severity": severity,
            "rule": rule, "detail": detail}


def vocabulary(doc, suppressed):
    for key, res in VOCAB_RES:
        if key in suppressed:
            continue
        for r in res:
            for m in r.finditer(doc.text):
                yield finding(doc, m.start(), "strip", "vocabulary", f'"{m.group(0)}"')


def hedging(doc, prose):
    for start, end in prose:
        for s, off in sentences(doc, start, end):
            hits = []
            for h, r in HEDGE_RES:
                hits += [h] * len(r.findall(s))
            if len(hits) >= 2:
                yield finding(doc, off, "strip", "hedging-stack",
                              f"{', '.join(hits)}: {short(s)}")


def em_dashes(doc, page_words):
    hits = [m.start() for m in EM_DASH_RE.finditer(doc.text)]
    words = len(WORD_RE.findall(doc.text))
    allowance = math.ceil(words / page_words)
    if len(hits) > allowance:
        yield finding(doc, hits[0], "strip", "em-dash-density",
                      f"{len(hits)} em dashes, allowance {allowance} for {words} words")


def negation(doc, prose):
    for start, end in prose:
        for s, off in sentences(doc, start, end):
            if s.rstrip("\"'’”)").endswith("?"):
                continue
            if any(r.search(s) for r in NEGATION_RES):
                yield finding(doc, off, "review", "negation-contrast", short(s))


def rhetorical(doc, prose):
    for start, end in prose:
        raw = doc.text[start:end]
        if LIST_MARKER_RE.match(raw):
            continue  # a list is not a paragraph
        sents = list(sentences(doc, start, end))
        if not sents:
            continue
        first, off = sents[0]
        low = plain(norm(raw))
        if any(low.startswith(o) for o in QUESTION_OPENERS):
            yield finding(doc, off, "review", "rhetorical-question", short(first))
        elif len(sents) == 1 and first.rstrip("\"'’”)").endswith("?"):
            yield finding(doc, off, "review", "rhetorical-question", short(first))


def symmetrical(doc, groups):
    for i, (kind, start, end) in enumerate(groups):
        if kind != "heading":
            continue
        title = HEADING_RE.match(doc.text[start:end]).group(2)
        key = " ".join(plain(title).split())
        if len(key.split()) < 3:
            continue
        last = None
        for kind2, s2, e2 in groups[i + 1:]:
            if kind2 == "heading":
                break
            if kind2 == "prose":
                sents = list(sentences(doc, s2, e2))
                if sents:
                    last = sents[-1]
        if last and key in " ".join(plain(last[0]).split()):
            yield finding(doc, last[1], "review", "symmetrical-ending",
                          f'heading "{title}" restated in: {short(last[0])}')


def check_doc(doc, suppressed, page_words):
    groups = blocks(doc)
    prose = [(s, e) for k, s, e in groups if k == "prose"]
    found = []
    found += vocabulary(doc, suppressed)
    found += hedging(doc, prose)
    found += em_dashes(doc, page_words)
    found += negation(doc, prose)
    found += rhetorical(doc, prose)
    found += symmetrical(doc, groups)
    found.sort(key=lambda f: f["line"])
    return found


def collect_files(paths):
    files = []
    for p in paths:
        if os.path.isdir(p):
            found = []
            for dirpath, dirnames, names in os.walk(p):
                dirnames[:] = sorted(d for d in dirnames
                                     if not d.startswith(".") and d not in SKIP_DIRS)
                found += [os.path.join(dirpath, n) for n in sorted(names)
                          if n.lower().endswith(".md")]
            if not found:
                raise UsageError(f"no markdown files under {p}")
            files += found
        elif os.path.isfile(p):
            files.append(p)
        else:
            raise UsageError(f"not a file or directory: {p}")
    return files


def suppressed_keys(allow):
    wanted = {a.strip().lower().replace("’", "'") for a in allow}
    return {key for key, forms in VOCABULARY if key in wanted or wanted & set(forms)}


def check(paths, allow=(), page_words=DEFAULT_PAGE_WORDS):
    suppressed = suppressed_keys(allow)
    findings = []
    for path in collect_files(paths):
        try:
            with open(path, encoding="utf-8") as f:
                raw = f.read()
        except (OSError, UnicodeDecodeError) as e:
            raise UsageError(f"cannot read {path}: {e}")
        doc = Doc(path.replace(os.sep, "/"), raw)
        findings += check_doc(doc, suppressed, page_words)
    return findings


def verdict(findings, strict):
    n_strip = sum(1 for f in findings if f["severity"] == "strip")
    n_review = len(findings) - n_strip
    failed = n_strip > 0 or (strict and n_review > 0)
    return failed, n_strip, n_review


def report(findings, strict, out=None):
    out = out or sys.stdout
    for f in findings:
        print(f"{f['path']}:{f['line']}: [{f['severity']}] {f['rule']}: {f['detail']}", file=out)
    failed, n_strip, n_review = verdict(findings, strict)
    if findings:
        print(file=out)
    print(f"{'FAIL' if failed else 'PASS'}: {n_strip} strip, {n_review} review", file=out)
    return failed


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("paths", nargs="+", metavar="PATH",
                    help="markdown file, or directory searched for *.md")
    ap.add_argument("--strict", action="store_true",
                    help="review findings also fail the run")
    ap.add_argument("--json", action="store_true", help="print the report as JSON")
    ap.add_argument("--allow", action="append", default=[], metavar="TERM",
                    help="suppress a strip-vocabulary term for this run (repeatable)")
    ap.add_argument("--page-words", type=int, default=DEFAULT_PAGE_WORDS,
                    help="words per page for the em-dash allowance (default %(default)s)")
    args = ap.parse_args(argv)
    if args.page_words <= 0:
        print("error: --page-words must be a positive integer", file=sys.stderr)
        return 2
    try:
        findings = check(args.paths, args.allow, args.page_words)
    except UsageError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    if args.json:
        failed, _, _ = verdict(findings, args.strict)
        json.dump({"pass": not failed, "findings": findings}, sys.stdout,
                  indent=2, ensure_ascii=False)
        print()
    else:
        failed = report(findings, args.strict)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
