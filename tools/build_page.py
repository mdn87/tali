#!/usr/bin/env python3
"""Rebuild the generated sections of a single-page HTML document from markdown.

Reads a JSON site config (default ./tali.site.json, see tali.site.example.json)
that maps <section class="doc" id="doc-..."> blocks to markdown sources, then
regenerates those sections in place, preserving the page shell (CSS, nav,
pager, JS) and any sections that have no markdown source. Paths in the config
are resolved relative to the config file's directory.

Markdown supported: # title (becomes the section h1), ## to ###### headings
(each gets an id of <section>--<slug> so links can target it), paragraphs,
*emphasis*, **strong**, `code`, fenced code (an info string becomes a class),
links, images, bullet and numbered lists with nesting and blank lines between
items, checklists, tables, blockquotes, horizontal rules, status chips, and
{.class} on its own line to tag the next table.

Usage:
    python build_page.py [--config tali.site.json]   # rebuild in place
    python build_page.py --check                     # report what would change, write nothing

Exit status: 0 ok, 2 config or source error.
"""

import argparse
import html
import json
import os
import re
import sys

DEFAULT_CONFIG = "tali.site.json"

# Populated by configure(); module-level so build_site.py and init_site.py can
# reuse the converter after loading the same config.
LINK_MAP = {}
CHIP_CLASSES = []
SKIP_PREFIXES = ()
SECTION_IDS = set()

# Set by convert() for the section being converted, so same-page anchors and
# heading ids are scoped to it.
CURRENT_SECTION = ""
_SLUGS_SEEN = set()


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
            "(see tali.site.example.json)"
        )
    try:
        cfg = _strip_comments(json.load(open(path, encoding="utf-8")))
    except json.JSONDecodeError as e:
        raise ConfigError(f"config is not valid JSON: {e}")
    cfg["_dir"] = os.path.dirname(os.path.abspath(path))
    return cfg


def require(cfg, key):
    if key not in cfg:
        raise ConfigError(f"config is missing required key: {key!r}")
    return cfg[key]


def configure(cfg):
    """Point the converter at this config's link map, chips, and skip list."""
    global LINK_MAP, CHIP_CLASSES, SKIP_PREFIXES, SECTION_IDS
    LINK_MAP = cfg.get("link_map", {})
    CHIP_CLASSES = [(c["label"], c["class"]) for c in cfg.get("chips", [])]
    SKIP_PREFIXES = tuple(cfg.get("skip_prefixes", []))
    SECTION_IDS = set(cfg.get("section_sources", {})) | {
        v.lstrip("#") for v in LINK_MAP.values()
    }


def esc(s):
    return html.escape(s, quote=False)


def slug(text):
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return text or "section"


def anchor(section_id, fragment=""):
    return f"#{section_id}--{fragment}" if fragment else f"#{section_id}"


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

    # images before links, or the link pattern eats them and leaves the "!"
    text = re.sub(
        r"!\[([^\]]*)\]\(([^)\s]+)\)",
        lambda m: f'<img src="{m.group(2)}" alt="{m.group(1)}">',
        text,
    )

    def linkrepl(m):
        label, target = m.group(1), m.group(2)
        path, _, frag = target.partition("#")
        base = path.split("/")[-1]
        if not path:
            # "#frag": a section id passes through, anything else is a
            # heading inside the section being converted
            if frag in SECTION_IDS or not CURRENT_SECTION:
                href = target
            else:
                href = anchor(CURRENT_SECTION, frag)
        elif base in LINK_MAP:
            href = anchor(LINK_MAP[base].lstrip("#"), frag)
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


BULLET = re.compile(r"^(\s*)[-*]\s+(.*)$")
ORDERED = re.compile(r"^(\s*)\d+[.)]\s+(.*)$")
CHECKBOX = re.compile(r"^\[[ xX]\]\s*")
HRULE = re.compile(r"^(-{3,}|\*{3,}|_{3,})\s*$")
HEADING = re.compile(r"^(#{2,6})\s+(.*)$")
BLOCK_START = re.compile(r"^(#{2,6}\s|[-*]\s|\d+[.)]\s|\||>|```|\{\.)")


def list_kind(line):
    """(kind, indent, item text) when the line opens a list item, else None."""
    m = BULLET.match(line)
    if m:
        return "ul", len(m.group(1).expandtabs(4)), m.group(2)
    m = ORDERED.match(line)
    if m:
        return "ol", len(m.group(1).expandtabs(4)), m.group(2)
    return None


def parse_list(lines, i, kind, indent):
    """Parse the list whose first item is lines[i]. Returns (html, next i).

    Items at a deeper indent become a nested list inside the current item;
    indented non-item lines continue the current item; blank lines end the
    list unless the next non-blank line is another item of this same list.
    """
    items = []
    is_check = False
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            j = i
            while j < len(lines) and not lines[j].strip():
                j += 1
            k = list_kind(lines[j]) if j < len(lines) else None
            if k and k[0] == kind and k[1] == indent:
                i = j
                continue
            break
        k = list_kind(line)
        if k and k[1] == indent:
            if k[0] != kind:
                break
            text = k[2]
            if CHECKBOX.match(text):
                is_check = is_check or not items
                text = CHECKBOX.sub("", text)
            items.append([text, ""])
            i += 1
            continue
        if k and k[1] > indent and items:
            sub, i = parse_list(lines, i, k[0], k[1])
            items[-1][1] += "\n" + sub
            continue
        if items and line.startswith((" ", "\t")) and not k:
            items[-1][0] += " " + line.strip()
            i += 1
            continue
        break
    cls = ' class="check"' if is_check else ""
    out = [f"<{kind}{cls}>"]
    out += [f"    <li>{inline(t)}{c}</li>" for t, c in items]
    out.append(f"  </{kind}>")
    return "\n".join(out), i


def heading(level, text):
    global _SLUGS_SEEN
    base = slug(text)
    s, n = base, 1
    while s in _SLUGS_SEEN:
        n += 1
        s = f"{base}-{n}"
    _SLUGS_SEEN.add(s)
    hid = f' id="{CURRENT_SECTION}--{s}"' if CURRENT_SECTION else ""
    return f"<h{level}{hid}>{inline(text)}</h{level}>"


def convert(md, section_id):
    """Markdown body -> HTML fragment (h1 handled by caller)."""
    global CURRENT_SECTION, _SLUGS_SEEN
    CURRENT_SECTION = section_id
    _SLUGS_SEEN = set()

    lines = md.replace("\r\n", "\n").split("\n")
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

        if HRULE.match(s):
            out.append("<hr>")
            i += 1
            continue

        m = HEADING.match(s)
        if m:
            out.append(heading(len(m.group(1)), m.group(2)))
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

        # bullet, checklist, or numbered list (nested by indentation)
        k = list_kind(line)
        if k:
            block, i = parse_list(lines, i, k[0], k[1])
            out.append(block)
            continue

        # paragraph
        buf = []
        while i < len(lines) and lines[i].strip() and not BLOCK_START.match(
            lines[i].strip()
        ) and not HRULE.match(lines[i].strip()):
            buf.append(lines[i].strip())
            i += 1
        if not buf:  # a line the block rules claim but could not parse
            buf.append(s)
            i += 1
        para = inline(" ".join(buf))
        out.append(f"<p>{chipify(para)}</p>")

    return "\n  ".join(out)


def rebuild(page, cfg, sources_root=None):
    """Regenerate the mapped sections of a page from markdown.

    Returns (new page text, ids regenerated, ids changed, ids preserved).
    `sources_root` overrides the config's, so one shell can be filled from
    several voice directories.
    """
    root = os.path.abspath(
        os.path.join(cfg["_dir"], sources_root or cfg.get("sources_root", "."))
    )
    section_sources = require(cfg, "section_sources")
    page = page.replace("\r\n", "\n")  # a CRLF checkout must not read as "changed"

    missing = [
        f"{sid} ({rel})"
        for sid, rel in section_sources.items()
        if not os.path.isfile(os.path.join(root, rel))
    ]
    if missing:
        raise ConfigError(
            f"markdown source not found under {root}: " + ", ".join(missing)
        )

    head_end = page.find('<section class="doc"')
    if head_end == -1:
        raise ConfigError('page has no <section class="doc" id="doc-..."> blocks')
    tail_start = page.rfind("</section>") + len("</section>")
    head, sections_blob, tail = page[:head_end], page[head_end:tail_start], page[tail_start:]

    # split existing sections, keep their crumbs and any we don't regenerate
    parts = re.split(r'(?=<section class="doc" id="doc-)', sections_blob)
    parts = [p for p in parts if p.strip()]

    rebuilt, regenerated, changed, kept = [], [], [], []
    for part in parts:
        m = re.match(r'<section class="doc" id="doc-([^"]+)"', part)
        sid = m.group(1)
        if sid not in section_sources:
            rebuilt.append(part)
            kept.append(sid)
            continue

        crumb_m = re.search(r"(<p class=\"crumb\">.*?</p>)", part, re.S)
        crumb = crumb_m.group(1) if crumb_m else ""

        md = open(os.path.join(root, section_sources[sid]), encoding="utf-8").read()
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
        regenerated.append(sid)
        if new_part.strip() != part.strip():
            changed.append(sid)
        rebuilt.append(new_part)

    unmatched = [sid for sid in section_sources if sid not in regenerated]
    if unmatched:
        raise ConfigError(
            "section_sources lists ids with no <section id=\"doc-...\"> in the page: "
            + ", ".join(unmatched)
        )
    # one blank line between the last section and the tail, however many
    # rebuilds have run, so a second build is byte-identical to the first
    body = "".join(rebuilt).rstrip("\n") + "\n\n" + tail.lstrip("\n")
    return head + body, regenerated, changed, kept


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Rebuild the generated HTML sections of a page from its markdown sources."
    )
    ap.add_argument("--config", default=DEFAULT_CONFIG,
                    help="site config JSON (default: %(default)s)")
    ap.add_argument("--check", action="store_true",
                    help="report what would change, write nothing")
    args = ap.parse_args(argv)

    try:
        cfg = load_config(args.config)
        configure(cfg)
        page_path = os.path.join(cfg["_dir"], require(cfg, "page"))
        if not os.path.isfile(page_path):
            raise ConfigError(f"page not found: {page_path} (init_site.py creates one)")
        page = open(page_path, encoding="utf-8").read()
        result, regenerated, changed, kept = rebuild(page, cfg)
    except ConfigError as e:
        print(f"config error: {e}", file=sys.stderr)
        return 2

    print(f"regenerated from markdown: {len(regenerated)} (changed: {len(changed)})")
    print(f"preserved as-is: {len(kept)} -> {', '.join(kept) or '-'}")
    if args.check:
        print(f"(check mode, nothing written) size {len(page)} -> {len(result)}")
        return 0

    with open(page_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(result)
    print(f"wrote {page_path}: {len(page)} -> {len(result)} chars")
    return 0


if __name__ == "__main__":
    sys.exit(main())
