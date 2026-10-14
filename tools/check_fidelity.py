#!/usr/bin/env python3
"""Check that every voice copy of a document set still carries its fidelity items.

Reads a JSON fidelity config (default ./tali.fidelity.json, see
tali.fidelity.example.json) naming a source directory, one directory per voice
that mirrors it, and the document set's declared fidelity list. For every
source document and every voice, the voice copy must contain:

- every fenced code block in the source, verbatim;
- every inline code span, URL, and number in the source prose;
- every declared fidelity phrase (labels, fixed phrases, load-bearing
  qualifiers, distinctions) that occurs in the source.

Matching collapses whitespace, so rewrapped lines still match, and ignores
`*` emphasis outside code, so "*not* a sandbox" still carries "not a sandbox".
Paths in the config are resolved relative to the config file's directory.

This is the mechanical half of fidelity verification. It proves the verbatim
items survived; it cannot judge meaning drift between paraphrased sentences
(see skills/voice-mutate/references/fidelity-checklist.md).

Usage:
    python check_fidelity.py [--config tali.fidelity.json]
    python check_fidelity.py --voice plain        # check one voice only
    python check_fidelity.py --json               # machine-readable report

Exit status: 0 every check passed, 1 at least one fidelity break, 2 config error.
"""

import argparse
import json
import os
import re
import sys

DEFAULT_CONFIG = "tali.fidelity.json"

FENCE = re.compile(r"^(```|~~~)[^\n]*\n(.*?)^\1[ \t]*$", re.M | re.S)
INLINE_CODE = re.compile(r"(`+)(.+?)\1", re.S)
URL = re.compile(r"https?://[^\s<>)\]]+")
# 3, 26, 1.5, 3.12, 10,000, 40%; skip digits glued to letters (Sev-1, v2, mp3).
NUMBER = re.compile(r"(?<![\w.-])\d+(?:[.,]\d+)*%?(?![\w-])")
LIST_MARKER = re.compile(r"^\s*\d+[.)]\s+", re.M)
HEADING_MARKER = re.compile(r"^#{1,6}\s+", re.M)


class ConfigError(Exception):
    pass


def _strip_comments(node):
    """Drop keys starting with "_" so the commented example config loads as-is."""
    if isinstance(node, dict):
        return {k: _strip_comments(v) for k, v in node.items() if not k.startswith("_")}
    if isinstance(node, list):
        return [_strip_comments(v) for v in node]
    return node


def load_config(path):
    if not os.path.exists(path):
        raise ConfigError(
            f"config not found: {path} — pass --config PATH or create one "
            "(see tali.fidelity.example.json)"
        )
    try:
        cfg = _strip_comments(json.load(open(path, encoding="utf-8")))
    except json.JSONDecodeError as e:
        raise ConfigError(f"config is not valid JSON: {e}")
    cfg["_dir"] = os.path.dirname(os.path.abspath(path))
    for key in ("sources_root", "voices"):
        if key not in cfg:
            raise ConfigError(f"config is missing required key: {key!r}")
    if not isinstance(cfg["voices"], dict) or not cfg["voices"]:
        raise ConfigError("'voices' must map each voice key to a directory")
    return cfg


def resolve(cfg, rel):
    return os.path.normpath(os.path.join(cfg["_dir"], rel))


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read().replace("\r\n", "\n")


def squash(s):
    return " ".join(s.split())


def list_documents(cfg):
    root = resolve(cfg, cfg["sources_root"])
    if not os.path.isdir(root):
        raise ConfigError(f"sources_root is not a directory: {root}")
    docs = cfg.get("documents")
    if docs:
        for d in docs:
            if not os.path.isfile(os.path.join(root, d)):
                raise ConfigError(f"listed document not found in sources_root: {d}")
        return list(docs)
    found = []
    for dirpath, _, files in os.walk(root):
        for name in files:
            if name.lower().endswith(".md"):
                rel = os.path.relpath(os.path.join(dirpath, name), root)
                found.append(rel.replace(os.sep, "/"))
    if not found:
        raise ConfigError(f"no .md documents under sources_root: {root}")
    return sorted(found)


def split_code(text):
    """Return (fenced blocks, inline spans, prose with all code removed)."""
    fences = [m.group(2) for m in FENCE.finditer(text)]
    rest = FENCE.sub("\n", text)
    spans = [m.group(2).strip() for m in INLINE_CODE.finditer(rest)]
    prose = INLINE_CODE.sub(" ", rest)
    return fences, spans, prose


def matchable(text):
    """Whitespace-collapsed text with `*` emphasis removed outside code."""
    fences, spans, _ = split_code(text)
    plain = FENCE.sub("\n", text)
    plain = INLINE_CODE.sub(lambda m: m.group(0).replace("*", "\0"), plain)
    plain = plain.replace("*", "").replace("\0", "*")
    return squash(plain), [squash(f) for f in fences], spans


def extract_items(source, cfg, declared):
    """The fidelity items a voice copy of this source must carry, in order."""
    auto = {"code": True, "urls": True, "numbers": True, **cfg.get("auto", {})}
    fences, spans, prose = split_code(source)
    items = []
    if auto["code"]:
        items += [("code block", squash(f)) for f in fences if f.strip()]
        items += [("inline code", s) for s in dict.fromkeys(spans) if s]
    if auto["urls"]:
        items += [("url", u) for u in dict.fromkeys(URL.findall(prose))]
    if auto["numbers"]:
        bare = URL.sub(" ", prose)
        bare = LIST_MARKER.sub(" ", bare)
        bare = HEADING_MARKER.sub(" ", bare)
        items += [("number", n) for n in dict.fromkeys(NUMBER.findall(bare))]
    text, _, _ = matchable(source)
    for phrase in declared:
        if squash(phrase) in text:
            items.append(("fidelity phrase", squash(phrase)))
    return items


def present(kind, item, voice_text, voice_fences, voice_spans):
    if kind == "code block":
        return item in voice_fences
    if kind == "inline code":
        return item in voice_spans or item in voice_text
    if kind == "number":
        return re.search(r"(?<![\w.-])" + re.escape(item) + r"(?![\w-])", voice_text) is not None
    return item in voice_text


def declared_for(cfg, doc):
    fid = cfg.get("fidelity", {})
    return list(fid.get("all", [])) + list(fid.get("documents", {}).get(doc, []))


def waived(cfg, voice, doc, item):
    for w in cfg.get("waivers", []):
        if not w.get("reason"):
            raise ConfigError(f"waiver for {w.get('item')!r} has no reason")
        if w.get("item") == item and w.get("voice", voice) == voice and w.get("document", doc) == doc:
            return w["reason"]
    return None


def check(cfg, only_voice=None):
    docs = list_documents(cfg)
    src_root = resolve(cfg, cfg["sources_root"])
    voices = cfg["voices"]
    if only_voice:
        if only_voice not in voices:
            raise ConfigError(f"unknown voice {only_voice!r}; config has: {', '.join(voices)}")
        voices = {only_voice: voices[only_voice]}

    # A declared document phrase that the source itself lacks is a stale
    # fidelity list, not a voice failure; refuse to run on it.
    for doc, phrases in cfg.get("fidelity", {}).get("documents", {}).items():
        if doc not in docs:
            raise ConfigError(f"fidelity list names a document not in the set: {doc}")
        text, _, _ = matchable(read(os.path.join(src_root, doc)))
        for p in phrases:
            if squash(p) not in text:
                raise ConfigError(f"fidelity phrase not found in source {doc}: {p!r}")

    results = []
    for voice, vdir in voices.items():
        vroot = resolve(cfg, vdir)
        for doc in docs:
            source = read(os.path.join(src_root, doc))
            entry = {"voice": voice, "document": doc, "missing": [], "waived": [], "checked": 0}
            vpath = os.path.join(vroot, doc)
            if not os.path.isfile(vpath):
                entry["missing"].append({"kind": "document", "item": "voice copy does not exist"})
                results.append(entry)
                continue
            vtext, vfences, vspans = matchable(read(vpath))
            items = extract_items(source, cfg, declared_for(cfg, doc))
            entry["checked"] = len(items)
            for kind, item in items:
                if present(kind, item, vtext, vfences, vspans):
                    continue
                reason = waived(cfg, voice, doc, item)
                bucket = entry["waived"] if reason else entry["missing"]
                rec = {"kind": kind, "item": item}
                if reason:
                    rec["reason"] = reason
                bucket.append(rec)
            results.append(entry)
    return results


def short(item, width=90):
    return item if len(item) <= width else item[: width - 1] + "…"


def report(results, out=None):
    out = out or sys.stdout
    failed = 0
    for r in results:
        label = f"{r['voice']}/{r['document']}"
        if r["missing"]:
            failed += 1
            print(f"FAIL {label}", file=out)
            for m in r["missing"]:
                print(f"     missing {m['kind']}: {short(m['item'])}", file=out)
        else:
            print(f"PASS {label} ({r['checked']} items)", file=out)
        for w in r["waived"]:
            print(f"     waived {w['kind']}: {short(w['item'])} ({w['reason']})", file=out)
    total = len(results)
    verdict = "FAIL" if failed else "PASS"
    print(f"\n{verdict}: {total - failed}/{total} voice copies carry every fidelity item", file=out)
    return failed


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--config", default=DEFAULT_CONFIG)
    ap.add_argument("--voice", help="check only this voice key")
    ap.add_argument("--json", action="store_true", help="print the report as JSON")
    args = ap.parse_args(argv)
    try:
        cfg = load_config(args.config)
        results = check(cfg, args.voice)
    except ConfigError as e:
        print(f"config error: {e}", file=sys.stderr)
        return 2
    if args.json:
        failed = sum(1 for r in results if r["missing"])
        json.dump({"pass": not failed, "results": results}, sys.stdout, indent=2, ensure_ascii=False)
        print()
    else:
        failed = report(results)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
