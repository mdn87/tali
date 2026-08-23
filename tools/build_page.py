#!/usr/bin/env python3
"""Rebuild the generated sections of a single-page HTML document from markdown.

Reads a JSON site config (default ./tali.site.json, see tali.site.example.json)
that maps <section class="doc" id="doc-..."> blocks to markdown sources, then
regenerates those sections in place, preserving the page shell (CSS, nav,
pager, JS) and any sections that have no markdown source. Paths in the config
are resolved relative to the config file's directory.

Usage:
    python build_page.py [--config tali.site.json]   # rebuild in place
    python build_page.py --check                     # report what would change, write nothing
"""

import argparse
import html
import json
import os
import re

DEFAULT_CONFIG = "tali.site.json"

# Populated by configure(); module-level so build_site.py can reuse the
# converter after loading the same config.
LINK_MAP = {}
CHIP_CLASSES = []
SKIP_PREFIXES = ()


def _strip_comments(node):
    """Drop keys starting with "_" so the commented example config loads as-is."""
    if isinstance(node, dict):
        return {k: _strip_comments(v) for k, v in node.items() if not k.startswith("_")}
    if isinstance(node, list):
        return [_strip_comments(v) for v in node]
    return node


def load_config(path):
    if not os.path.exists(path):
        raise SystemExit(
            f"config not found: {path} — pass --config PATH or create one "
            "(see tali.site.example.json)"
        )
    cfg = _strip_comments(json.load(open(path, encoding="utf-8")))
    cfg["_dir"] = os.path.dirname(os.path.abspath(path))
    return cfg


def require(cfg, key):
    if key not in cfg:
        raise SystemExit(f"config is missing required key: {key!r}")
    return cfg[key]


def configure(cfg):
    """Point the converter at this config's link map, chips, and skip list."""
    global LINK_MAP, CHIP_CLASSES, SKIP_PREFIXES
    LINK_MAP = cfg.get("link_map", {})
    CHIP_CLASSES = [(c["label"], c["class"]) for c in cfg.get("chips", [])]
    SKIP_PREFIXES = tuple(cfg.get("skip_prefixes", []))


def esc(s):
    return html.escape(s, quote=False)


# inline HTML allowed to pass through the converter untouched
RAW_HTML = re.compile(r"</?(?:span|strong|em|code|br)\b[^>]*>")


def inline(text):
    """Convert markdown inline formatting to HTML.

    Code spans are protected from formatting, and a small set of inline HTML
    tags is passed through so source files can use status chips directly.
    """
    spans = []
    raw = []

    def stash(m):
        spans.append(m.group(1))
        return f"\x00{len(spans) - 1}\x00"

    def stash_raw(m):
        raw.append(m.group(0))
        return f"\x01{len(raw) - 1}\x01"

    text = re.sub(r"`([^`]+)`", stash, text)
    text = RAW_HTML.sub(stash_raw, text)
    text = esc(text)
    # links
    def linkrepl(m):
        label, target = m.group(1), m.group(2)
        base = target.split("/")[-1].split("#")[0]
        if target.startswith("#"):
            href = target
        elif base in LINK_MAP:
            href = LINK_MAP[base]
        elif target.startswith("http"):
            href = target
        else:
            return label  # unmapped local file: drop the link, keep the words
        return f'<a href="{href}">{label}</a>'

    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", linkrepl, text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![*\w])\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", text)
    for i, code in enumerate(spans):
        text = text.replace(f"\x00{i}\x00", f"<code>{esc(code)}</code>")
    for i, tag in enumerate(raw):
        text = text.replace(f"\x01{i}\x01", tag)
    return text


def chipify(html_text):
    """Turn a leading bold status label into its status chip."""
    for label, cls in CHIP_CLASSES:
        for tail in (".", ""):
            needle = f"<strong>{label}{tail}</strong>"
            if html_text.startswith(needle):
                return html_text.replace(
                    needle, f'<span class="chip {cls}">{label}{tail}</span>', 1
                )
    return html_text


def split_table_row(line):
    cells = line.strip().strip("|").split("|")
    return [c.strip() for c in cells]


def convert(md, section_id):
    """Markdown body -> HTML fragment (h1 handled by caller)."""
    lines = md.split("\n")
    out = []
    i = 0
    # drop title + frontmatter lines
    while i < len(lines):
        s = lines[i].strip()
        if s.startswith("# "):
            i += 1
            continue
        if (SKIP_PREFIXES and s.startswith(SKIP_PREFIXES)) or s == "":
            i += 1
            continue
        break

    pending_class = ""

    while i < len(lines):
        line = lines[i]
        s = line.strip()

        if not s:
            i += 1
            continue

        # {.classname} on its own line attaches a class to the next block
        m_cls = re.match(r"^\{\.([a-z][\w-]*)\}$", s)
        if m_cls:
            pending_class = m_cls.group(1)
            i += 1
            continue

        if SKIP_PREFIXES and s.startswith(SKIP_PREFIXES):
            i += 1
            continue

        # fenced code; an info string becomes a class (```equation -> class="equation")
        if s.startswith("```"):
            info = s[3:].strip()
            i += 1
            buf = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            cls = f' class="{info}"' if info and info.isalpha() else ""
            out.append(f"<pre{cls}>" + esc("\n".join(buf)) + "</pre>")
            continue

        # headings
        m = re.match(r"^(#{2,4})\s+(.*)$", s)
        if m:
            lvl = len(m.group(1))
            out.append(f"<h{lvl}>{inline(m.group(2))}</h{lvl}>")
            i += 1
            continue

        # blockquote
        if s.startswith(">"):
            buf = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip().lstrip(">").strip())
                i += 1
            out.append(f"<blockquote><p>{inline(' '.join(buf))}</p></blockquote>")
            continue

        # table
        if s.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(lines[i])
                i += 1
            if len(rows) >= 2 and set(rows[1].replace("|", "").strip()) <= set("-: "):
                head = split_table_row(rows[0])
                body = rows[2:]
            else:
                head, body = None, rows
            wrap_cls = f"tablewrap {pending_class}".strip()
            pending_class = ""
            t = [f'<div class="{wrap_cls}"><table>']
            if head:
                t.append(
                    "<tr>" + "".join(f"<th>{inline(c)}</th>" for c in head) + "</tr>"
                )
            for r in body:
                cells = split_table_row(r)
                t.append(
                    "<tr>" + "".join(f"<td>{inline(c)}</td>" for c in cells) + "</tr>"
                )
            t.append("</table></div>")
            out.append("\n    ".join(t))
            continue

        # checklist / unordered list
        if re.match(r"^[-*]\s+", s):
            is_check = bool(re.match(r"^[-*]\s+\[[ xX]\]", s))
            items = []
            while i < len(lines) and re.match(r"^[-*]\s+", lines[i].strip()):
                item = re.sub(r"^[-*]\s+", "", lines[i].strip())
                item = re.sub(r"^\[[ xX]\]\s*", "", item)
                i += 1
                # continuation lines
                while (
                    i < len(lines)
                    and lines[i].startswith(("  ", "\t"))
                    and lines[i].strip()
                    and not re.match(r"^[-*]\s+", lines[i].strip())
                ):
                    item += " " + lines[i].strip()
                    i += 1
                items.append(item)
            cls = ' class="check"' if is_check else ""
            out.append(
                f"<ul{cls}>\n    "
                + "\n    ".join(f"<li>{inline(x)}</li>" for x in items)
                + "\n  </ul>"
            )
            continue

        # ordered list
        if re.match(r"^\d+\.\s+", s):
            items = []
            while i < len(lines) and re.match(r"^\d+\.\s+", lines[i].strip()):
                item = re.sub(r"^\d+\.\s+", "", lines[i].strip())
                i += 1
                while (
                    i < len(lines)
                    and lines[i].startswith(("  ", "\t"))
                    and lines[i].strip()
                    and not re.match(r"^\d+\.\s+", lines[i].strip())
                ):
                    item += " " + lines[i].strip()
                    i += 1
                items.append(item)
            out.append(
                "<ol>\n    "
                + "\n    ".join(f"<li>{inline(x)}</li>" for x in items)
                + "\n  </ol>"
            )
            continue

        # paragraph
        buf = []
        while i < len(lines) and lines[i].strip() and not re.match(
            r"^(#{2,4}\s|[-*]\s|\d+\.\s|\||>|```)", lines[i].strip()
        ):
            buf.append(lines[i].strip())
            i += 1
        para = inline(" ".join(buf))
        out.append(f"<p>{chipify(para)}</p>")

    return "\n  ".join(out)


def main():
    ap = argparse.ArgumentParser(
        description="Rebuild the generated HTML sections of a page from its markdown sources."
    )
    ap.add_argument("--config", default=DEFAULT_CONFIG,
                    help="site config JSON (default: %(default)s)")
    ap.add_argument("--check", action="store_true",
                    help="report what would change, write nothing")
    args = ap.parse_args()

    cfg = load_config(args.config)
    configure(cfg)

    page_path = os.path.join(cfg["_dir"], require(cfg, "page"))
    sources_root = os.path.abspath(
        os.path.join(cfg["_dir"], cfg.get("sources_root", "."))
    )
    section_sources = require(cfg, "section_sources")

    page = open(page_path, encoding="utf-8").read()

    head_end = page.find('<section class="doc"')
    tail_start = page.rfind("</section>") + len("</section>")
    head, sections_blob, tail = (
        page[:head_end],
        page[head_end:tail_start],
        page[tail_start:],
    )

    # split existing sections, keep their crumbs and any we don't regenerate
    parts = re.split(r'(?=<section class="doc" id="doc-)', sections_blob)
    parts = [p for p in parts if p.strip()]

    rebuilt, changed, kept = [], [], []
    for part in parts:
        m = re.match(r'<section class="doc" id="doc-([^"]+)"', part)
        sid = m.group(1)
        if sid not in section_sources:
            rebuilt.append(part)
            kept.append(sid)
            continue

        crumb_m = re.search(r"(<p class=\"crumb\">.*?</p>)", part, re.S)
        crumb = crumb_m.group(1) if crumb_m else ""

        md_path = os.path.join(sources_root, section_sources[sid])
        md = open(md_path, encoding="utf-8").read()
        title_m = re.search(r"^#\s+(.*)$", md, re.M)
        title = inline(title_m.group(1)) if title_m else sid
        body = convert(md, sid)

        new_part = (
            f'<section class="doc" id="doc-{sid}" hidden>\n'
            f"  {crumb}\n"
            f"  <h1>{title}</h1>\n"
            f"  {body}\n"
            f"</section>\n\n"
        )
        if new_part.strip() != part.strip():
            changed.append(sid)
        rebuilt.append(new_part)

    result = head + "".join(rebuilt) + tail

    print(f"regenerated from markdown: {len(changed)}")
    print(f"preserved as-is: {len(kept)} -> {', '.join(kept)}")
    if args.check:
        print(f"(check mode, nothing written) size {len(page)} -> {len(result)}")
        return

    open(page_path, "w", encoding="utf-8").write(result)
    print(f"wrote {page_path}: {len(page)} -> {len(result)} chars")


if __name__ == "__main__":
    main()
