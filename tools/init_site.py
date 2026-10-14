#!/usr/bin/env python3
"""Scaffold a tali publish project from a directory of markdown documents.

Creates, in the output directory:

  <page>               the single-page shell from tali.page.template.html,
                       with one section per markdown file, already filled
  tali.site.json       config for build_page.py, build_site.py, build_pdf.py
  tali.fidelity.json   config for check_fidelity.py, one directory per voice

Section ids come from the file paths (guides/setup.md -> guides-setup), nav
groups from the top-level directory (root files are grouped as Documents),
titles from each file's first "# " line. Voices are expected under
voices/<name>/ mirroring the sources, which is what check_fidelity.py and the
site's per-voice versions read. Nothing already present is overwritten unless
--force is given.

Usage:
    python init_site.py --sources docs [--out .] [--title "Team Handbook"]
                        [--subtitle "..."] [--page handbook.html]
                        [--voices plain,casual] [--force]

Exit status: 0 ok, 2 bad arguments or a file already exists.
"""

import argparse
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_page  # noqa: E402
from build_page import ConfigError  # noqa: E402

TEMPLATE = os.path.join(HERE, "tali.page.template.html")

DEFAULT_CHIPS = [
    {"label": "Recommended", "class": "ok"},
    {"label": "Use with care", "class": "cond"},
    {"label": "Ask first", "class": "case"},
    {"label": "Not recommended", "class": "no"},
]


def section_id(rel):
    stem = os.path.splitext(rel)[0]
    return build_page.slug(stem.replace("/", "-"))


def group_label(rel):
    parts = rel.split("/")
    if len(parts) == 1:
        return "Documents"
    return re.sub(r"[-_]+", " ", parts[0]).strip().title()


def doc_title(path, rel):
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("# "):
                return line[2:].strip()
    return os.path.splitext(os.path.basename(rel))[0].replace("-", " ").replace("_", " ").title()


def find_documents(sources):
    """Markdown files relative to `sources`: root files first (README first), then subdirectories."""
    found = []
    for dirpath, dirs, files in os.walk(sources):
        dirs.sort()
        for name in sorted(files):
            if name.lower().endswith(".md"):
                rel = os.path.relpath(os.path.join(dirpath, name), sources).replace(os.sep, "/")
                found.append(rel)
    root = [r for r in found if "/" not in r]
    root.sort(key=lambda r: (r.lower() != "readme.md", r.lower()))
    nested = sorted(r for r in found if "/" in r)
    return root + nested


def repo_relative(path):
    """Path relative to the enclosing git repo, or just its basename."""
    try:
        top = subprocess.run(
            ["git", "-C", os.path.dirname(path), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, encoding="utf-8",
        )
    except FileNotFoundError:
        return os.path.basename(path)
    if top.returncode != 0:
        return os.path.basename(path)
    return os.path.relpath(path, top.stdout.strip()).replace(os.sep, "/")


def site_config(args, docs, out, page_path):
    sids = {rel: section_id(rel) for rel in docs}
    link_map, collisions = {}, []
    for rel, sid in sids.items():
        base = os.path.basename(rel)
        if base in link_map:
            collisions.append(rel)
            continue
        link_map[base] = f"#{sid}"
    stem = os.path.splitext(os.path.basename(page_path))[0]
    versions = [{
        "key": "orig", "file": "index.html", "url": "/", "label": "Original",
        "subtitle_suffix": "", "ref": None,
    }]
    for v in args.voices:
        versions.append({
            "key": v, "file": f"{v}.html", "url": f"/{v}", "label": v.replace("-", " ").title(),
            "subtitle_suffix": f" · {v} voice", "sources_root": f"voices/{v}",
        })
    cfg = {
        "page": os.path.basename(page_path),
        "sources_root": os.path.relpath(args.sources, out).replace(os.sep, "/"),
        "section_sources": {sid: rel for rel, sid in sids.items()},
        "link_map": link_map,
        "chips": DEFAULT_CHIPS,
        "skip_prefixes": [],
        "site_dir": "site",
        "covers_dir": "covers",
        "cover_section": sids[docs[0]],
        "page_repo_path": repo_relative(page_path),
        "versions": versions,
        "static_assets": ["robots.txt", f"{stem}.pdf"],
        "pdf": f"{stem}.pdf",
        "pdf_label": "draft",
        "title_page": {"title": args.title, "subtitle": args.subtitle,
                       "source": cfg_source(args, out), "note": ""},
    }
    return cfg, collisions


def cfg_source(args, out):
    return os.path.relpath(args.sources, out).replace(os.sep, "/")


def fidelity_config(args, out):
    return {
        "sources_root": os.path.relpath(args.sources, out).replace(os.sep, "/"),
        "voices": {v: f"voices/{v}" for v in args.voices},
        "skeletons_dir": "skeletons",
        "fidelity": {"all": [], "documents": {}},
        "waivers": [],
    }


def page_shell(args, docs, sources):
    nav, sections, current_group = [], [], None
    for rel in docs:
        sid, group = section_id(rel), group_label(rel)
        title = build_page.esc(doc_title(os.path.join(sources, rel), rel))
        if group != current_group:
            nav.append(f'  <div class="grp-label">{build_page.esc(group)}</div>')
            current_group = group
        nav.append(f'  <a class="navlink" href="#{sid}">{title}</a>')
        sections.append(
            f'<section class="doc" id="doc-{sid}" hidden>\n'
            f'  <p class="crumb">{build_page.esc(group)} / {title}</p>\n'
            f"  <h1>{title}</h1>\n"
            f"  <p>Run build_page.py to fill this section from {build_page.esc(rel)}.</p>\n"
            f"</section>\n"
        )
    shell = open(TEMPLATE, encoding="utf-8").read()
    return (
        shell.replace("{{TITLE}}", build_page.esc(args.title))
        .replace("{{SUBTITLE}}", build_page.esc(args.subtitle))
        .replace("{{NAV}}", "\n".join(nav))
        .replace("{{SECTIONS}}", "\n".join(sections))
    )


def write_json(path, data):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--sources", required=True, help="directory of markdown documents")
    ap.add_argument("--out", default=".", help="where to write the page and configs (default: .)")
    ap.add_argument("--title", default="Handbook")
    ap.add_argument("--subtitle", default="")
    ap.add_argument("--page", default="handbook.html", help="page filename (default: %(default)s)")
    ap.add_argument("--voices", default="plain",
                    help="comma-separated voice names, kept under voices/<name>/ (default: %(default)s)")
    ap.add_argument("--force", action="store_true", help="overwrite existing files")
    args = ap.parse_args(argv)
    args.voices = [v.strip() for v in args.voices.split(",") if v.strip()]

    try:
        sources = os.path.abspath(args.sources)
        out = os.path.abspath(args.out)
        if not os.path.isdir(sources):
            raise ConfigError(f"sources is not a directory: {sources}")
        docs = find_documents(sources)
        if not docs:
            raise ConfigError(f"no .md files under {sources}")
        os.makedirs(out, exist_ok=True)
        page_path = os.path.join(out, args.page)
        targets = [page_path, os.path.join(out, "tali.site.json"), os.path.join(out, "tali.fidelity.json")]
        existing = [t for t in targets if os.path.exists(t)]
        if existing and not args.force:
            raise ConfigError("already exists (pass --force to overwrite): " + ", ".join(existing))

        cfg, collisions = site_config(args, docs, out, page_path)
        shell = page_shell(args, docs, sources)
        cfg_for_build = dict(cfg, _dir=out)
        build_page.configure(cfg_for_build)
        filled = build_page.rebuild(shell, cfg_for_build)[0]
    except ConfigError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    with open(page_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(filled)
    write_json(targets[1], cfg)
    write_json(targets[2], fidelity_config(args, out))

    print(f"wrote {args.page} with {len(docs)} sections, tali.site.json, tali.fidelity.json in {out}")
    if collisions:
        print("note: these files share a basename with an earlier one, so links to them "
              "are not mapped: " + ", ".join(collisions))
    print("next: put each voice's copies under voices/<name>/ mirroring the sources, "
          "fill the fidelity list in tali.fidelity.json, then run build_page.py, "
          "build_site.py, build_pdf.py and check_fidelity.py from this directory")
    return 0


if __name__ == "__main__":
    sys.exit(main())
