#!/usr/bin/env python3
"""Check that every voice copy of a document set still carries its fidelity items.

Reads a JSON fidelity config (default ./tali.fidelity.json, see
tali.fidelity.example.json) naming the source documents, one location per
voice that mirrors them, and the document set's declared fidelity list. For
every source document and every voice, the voice copy must contain:

- every fenced code block in the source, verbatim;
- every inline code span, URL, and number in the source prose;
- every declared fidelity phrase (labels, fixed phrases, load-bearing
  qualifiers, distinctions) that occurs in the source;
- every mechanically checkable item of the document's fact skeleton when a
  skeletons directory is configured: the Verbatim, Labels, Fixed phrases and
  Qualifiers sections. Claims and Distinctions stay with the human verifier.

Sources and voices live in the working tree or at a git ref. "sources_ref"
reads the sources from a commit instead of the checkout; a voice given as
{"ref": "voice-casual"} reads its copies from that branch at the same paths
(the voice-review branch-per-voice pattern), and {"ref": ..., "dir": ...}
from another directory of the repository. The config must sit inside the
repository for refs to resolve.

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
import posixpath
import re
import subprocess
import sys

DEFAULT_CONFIG = "tali.fidelity.json"

FENCE = re.compile(r"^(```|~~~)[^\n]*\n(.*?)^\1[ \t]*$", re.M | re.S)
INLINE_CODE = re.compile(r"(`+)(.+?)\1", re.S)
URL = re.compile(r"https?://[^\s<>)\]]+")
# 3, 26, 1.5, 3.12, 10,000, 40%; skip digits glued to letters (Sev-1, v2, mp3).
NUMBER = re.compile(r"(?<![\w.-])\d+(?:[.,]\d+)*%?(?![\w-])")
LIST_MARKER = re.compile(r"^\s*\d+[.)]\s+", re.M)
HEADING_MARKER = re.compile(r"^#{1,6}\s+", re.M)

SKELETON_HEADING = re.compile(r"^##\s+(.+?)\s*$")
SKELETON_BULLET = re.compile(r"^\s*[-*]\s+(.*)$")
SKELETON_ITEM = re.compile(r"^([A-Z]+\d+):\s*(.+?)\s*$")
# Skeleton sections the script checks, and the item kind each one reports.
# Claims and Distinctions are judgment calls and stay with the verifier.
SKELETON_KINDS = {
    "verbatim": "skeleton verbatim",
    "labels": "skeleton label",
    "fixed phrases": "skeleton fixed phrase",
    "qualifiers": "skeleton qualifier",
}


class ConfigError(Exception):
    pass


def _strip_comments(node):
    """Drop keys starting with "_" so the commented example config loads as-is."""
    if isinstance(node, dict):
        return {k: _strip_comments(v) for k, v in node.items() if not k.startswith("_")}
    if isinstance(node, list):
        return [_strip_comments(v) for v in node]
    return node


def voice_spec(key, spec, sources_root):
    """Normalize a voice entry to {"dir": ..., "ref": ... or None}."""
    if isinstance(spec, str):
        return {"dir": spec, "ref": None}
    if isinstance(spec, dict):
        unknown = sorted(set(spec) - {"ref", "dir"})
        if unknown:
            raise ConfigError(f"voice {key!r} has unknown key(s) {unknown}; allowed: ref, dir")
        for k in ("ref", "dir"):
            if k in spec and not isinstance(spec[k], str):
                raise ConfigError(f"voice {key!r}: {k!r} must be a string")
        if not spec.get("ref") and not spec.get("dir"):
            raise ConfigError(f"voice {key!r} needs a 'ref', a 'dir', or both")
        return {"dir": spec.get("dir") or sources_root, "ref": spec.get("ref") or None}
    raise ConfigError(f"voice {key!r} must be a directory string or a {{ref, dir}} object")


def load_config(path):
    if not os.path.exists(path):
        raise ConfigError(
            f"config not found: {path} — pass --config PATH or create one "
            "(see tali.fidelity.example.json)"
        )
    try:
        with open(path, encoding="utf-8") as f:
            cfg = _strip_comments(json.load(f))
    except json.JSONDecodeError as e:
        raise ConfigError(f"config is not valid JSON: {e}")
    cfg["_dir"] = os.path.dirname(os.path.abspath(path))
    for key in ("sources_root", "voices"):
        if key not in cfg:
            raise ConfigError(f"config is missing required key: {key!r}")
    if not isinstance(cfg["voices"], dict) or not cfg["voices"]:
        raise ConfigError("'voices' must map each voice key to a directory or a {ref, dir} object")
    cfg["voices"] = {k: voice_spec(k, v, cfg["sources_root"]) for k, v in cfg["voices"].items()}
    if "sources_ref" in cfg and not isinstance(cfg["sources_ref"], str):
        raise ConfigError("'sources_ref' must be a git ref string")
    return cfg


def resolve(cfg, rel):
    return os.path.normpath(os.path.join(cfg["_dir"], rel))


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read().replace("\r\n", "\n")


def squash(s):
    return " ".join(s.split())


# --- document trees: a working-tree directory or a directory at a git ref ---

def git(cfg, *args, ref=None):
    """Run git at the repository top level; any failure is a config error."""
    cwd = cfg.get("_toplevel", cfg["_dir"])
    try:
        proc = subprocess.run(
            ["git", *args], cwd=cwd, capture_output=True,
            text=True, encoding="utf-8", errors="replace",
        )
    except FileNotFoundError:
        raise ConfigError("git is not on PATH; sources_ref and ref voices need it") from None
    if proc.returncode != 0:
        where = f" at ref {ref!r}" if ref else ""
        raise ConfigError(f"git failed{where} ({' '.join(args)}): {proc.stderr.strip()}")
    return proc.stdout


def toplevel(cfg):
    if "_toplevel" not in cfg:
        cfg["_toplevel"] = os.path.realpath(git(cfg, "rev-parse", "--show-toplevel").strip())
    return cfg["_toplevel"]


def repo_relpath(cfg, rel):
    """Config-relative path -> path relative to the repository top level, POSIX form."""
    top = toplevel(cfg)
    try:
        inside = os.path.relpath(os.path.realpath(resolve(cfg, rel)), top)
    except ValueError:  # another drive on Windows
        inside = ".."
    inside = inside.replace(os.sep, "/")
    if inside == ".." or inside.startswith("../"):
        raise ConfigError(f"{rel!r} is outside the git repository at {top}")
    return inside


class DirTree:
    """Documents under a working-tree directory."""

    ref = None

    def __init__(self, root):
        self.root = self.location = root

    def list_md(self):
        found = []
        for dirpath, _, files in os.walk(self.root):
            for name in files:
                if name.lower().endswith(".md"):
                    rel = os.path.relpath(os.path.join(dirpath, name), self.root)
                    found.append(rel.replace(os.sep, "/"))
        return sorted(found)

    def has(self, doc):
        return os.path.isfile(os.path.join(self.root, doc))

    def read(self, doc):
        return read(os.path.join(self.root, doc))


class GitTree:
    """Documents under one directory of the repository at a git ref."""

    def __init__(self, cfg, ref, rel):
        self.cfg, self.ref = cfg, ref
        self.prefix = self.location = repo_relpath(cfg, rel)
        self._names = None

    def _listing(self):
        if self._names is None:
            args = ["ls-tree", "-r", "-z", "--name-only", self.ref]
            if self.prefix != ".":
                args += ["--", self.prefix]
            out = git(self.cfg, *args, ref=self.ref)
            base = "" if self.prefix == "." else self.prefix + "/"
            self._names = {
                p[len(base):] for p in out.split("\0") if p.startswith(base) and p != base
            }
        return self._names

    def list_md(self):
        return sorted(p for p in self._listing() if p.lower().endswith(".md"))

    def has(self, doc):
        return doc in self._listing()

    def read(self, doc):
        obj = posixpath.normpath(posixpath.join(self.prefix, doc))
        return git(self.cfg, "show", f"{self.ref}:{obj}", ref=self.ref).replace("\r\n", "\n")


def source_tree(cfg):
    if cfg.get("sources_ref"):
        return GitTree(cfg, cfg["sources_ref"], cfg["sources_root"])
    root = resolve(cfg, cfg["sources_root"])
    if not os.path.isdir(root):
        raise ConfigError(f"sources_root is not a directory: {root}")
    return DirTree(root)


def voice_tree(cfg, spec):
    if spec["ref"]:
        return GitTree(cfg, spec["ref"], spec["dir"])
    return DirTree(resolve(cfg, spec["dir"]))


def list_documents(cfg, tree):
    at = f" at ref {tree.ref!r}" if tree.ref else ""
    docs = cfg.get("documents")
    if docs:
        for d in docs:
            if not tree.has(d):
                raise ConfigError(f"listed document not found in sources_root{at}: {d}")
        return list(docs)
    found = tree.list_md()
    if not found:
        raise ConfigError(f"no .md documents under sources_root{at}: {tree.location}")
    return found


# --- text matching ---

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


def contains(text, fences, spans, phrase):
    """Whether a phrase occurs in the prose, a fenced block, or an inline span."""
    return (
        phrase in text
        or any(phrase in f for f in fences)
        or any(phrase in squash(s) for s in spans)
    )


# --- fact skeletons ---

def skeleton_path(cfg, doc):
    sdir = cfg.get("skeletons_dir")
    if not sdir:
        return None
    stem = re.sub(r"\.md$", "", doc, flags=re.I)
    path = os.path.join(resolve(cfg, sdir), stem + ".skeleton.md")
    return path if os.path.isfile(path) else None


def parse_skeleton(path):
    """(kind, phrase) pairs from the mechanically checkable skeleton sections."""
    items, kind = [], None
    for line in read(path).split("\n"):
        h = SKELETON_HEADING.match(line)
        if h:
            kind = SKELETON_KINDS.get(h.group(1).lower())
            continue
        if kind is None:
            continue
        b = SKELETON_BULLET.match(line)
        if not b:
            continue
        m = SKELETON_ITEM.match(b.group(1))
        if not m:
            raise ConfigError(
                f"skeleton bullet without an '<ID>: ' prefix in {path}: {line.strip()!r}"
            )
        text = m.group(2)
        if len(text) >= 2 and text[0] == "`" and text[-1] == "`":
            text = text[1:-1].strip()
        if not text:
            raise ConfigError(f"skeleton item {m.group(1)} in {path} has no text")
        items.append((kind, squash(text)))
    return items


# --- the check ---

def extract_items(source, cfg, declared, skeleton=()):
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
    text, sq_fences, _ = matchable(source)
    for phrase in dict.fromkeys(squash(p) for p in declared):
        if contains(text, sq_fences, spans, phrase):
            items.append(("fidelity phrase", phrase))
    # A skeleton item that repeats something already required is one item.
    seen = {item for _, item in items}
    for kind, phrase in skeleton:
        if phrase not in seen:
            items.append((kind, phrase))
            seen.add(phrase)
    return items


def present(kind, item, voice_text, voice_fences, voice_spans):
    if kind == "code block":
        return item in voice_fences
    if kind == "inline code":
        return item in voice_spans or item in voice_text
    if kind == "number":
        return re.search(r"(?<![\w.-])" + re.escape(item) + r"(?![\w-])", voice_text) is not None
    return contains(voice_text, voice_fences, voice_spans, item)


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
    src = source_tree(cfg)
    docs = list_documents(cfg, src)
    voices = cfg["voices"]
    if only_voice:
        if only_voice not in voices:
            raise ConfigError(f"unknown voice {only_voice!r}; config has: {', '.join(voices)}")
        voices = {only_voice: voices[only_voice]}

    sources = {doc: src.read(doc) for doc in docs}
    parsed = {doc: matchable(sources[doc]) for doc in docs}

    # A declared document phrase that the source itself lacks is a stale
    # fidelity list, not a voice failure; refuse to run on it.
    for doc, phrases in cfg.get("fidelity", {}).get("documents", {}).items():
        if doc not in docs:
            raise ConfigError(f"fidelity list names a document not in the set: {doc}")
        text, fences, spans = parsed[doc]
        for p in phrases:
            if not contains(text, fences, spans, squash(p)):
                raise ConfigError(f"fidelity phrase not found in source {doc}: {p!r}")

    # Same for a fact skeleton: it was built from the source, so an item the
    # source no longer carries means the skeleton drifted, not the voice.
    skeletons = {}
    for doc in docs:
        path = skeleton_path(cfg, doc)
        skeletons[doc] = parse_skeleton(path) if path else []
        text, fences, spans = parsed[doc]
        for _, phrase in skeletons[doc]:
            if not contains(text, fences, spans, phrase):
                raise ConfigError(f"skeleton phrase not found in source {doc}: {phrase!r}")

    results = []
    for voice, spec in voices.items():
        tree = voice_tree(cfg, spec)
        for doc in docs:
            entry = {"voice": voice, "document": doc, "missing": [], "waived": [], "checked": 0}
            if not tree.has(doc):
                entry["missing"].append({"kind": "document", "item": "voice copy does not exist"})
                results.append(entry)
                continue
            vtext, vfences, vspans = matchable(tree.read(doc))
            items = extract_items(sources[doc], cfg, declared_for(cfg, doc), skeletons[doc])
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
