#!/usr/bin/env python3
"""Render the built webpage into a single print-ready PDF manual.

Unhides every section, strips the single-page-app JS, adds print styling,
and generates the title page and contents from the page's own nav so the
manual can never drift from the site. Rendering uses headless Chrome or
Edge. The page filename, PDF filename, title-page text, and default
edition label all come from the JSON site config; if the config's site
directory exists, the PDF is copied there too.

Usage:  python build_pdf.py [--config tali.site.json] [--label "draft 2026-08-23"]
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import tempfile

DEFAULT_CONFIG = "tali.site.json"

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
]

PRINT_CSS = """
<style>
  html, body { background:#FFFFFF; }
  .side, .pager, #pager { display:none !important; }
  .app { display:block !important; }
  main { margin:0 !important; max-width:100% !important; padding:0 !important; }
  section.doc {
    display:block !important;
    page-break-before:always; break-before:page;
    max-width:7.4in; margin:0 auto; padding:.2in 0 .4in 0;
  }
  section.doc:first-of-type { page-break-before:avoid; break-before:avoid; }
  .tablewrap { overflow-x:visible !important; }
  table { font-size:9.5pt; }
  pre { white-space:pre-wrap; }
  a { color:inherit; text-decoration:none; }
  .titlepage {
    page-break-after:always; break-after:page;
    display:flex; flex-direction:column; justify-content:center;
    min-height:8in; max-width:7.4in; margin:0 auto;
    font-family:'Public Sans',system-ui,sans-serif;
  }
  .titlepage h1 { font-size:34pt; margin:0 0 12pt 0; color:#1B2530; }
  .titlepage p { font-size:12pt; color:#5A6878; margin:4pt 0; }
  .toc { max-width:7.4in; margin:0 auto; page-break-after:always; break-after:page;
         font-family:'Public Sans',system-ui,sans-serif; }
  .toc h2 { font-size:16pt; color:#1B2530; }
  .toc ul { list-style:none; padding-left:0; column-count:2; column-gap:32pt;
            font-size:10pt; line-height:1.9; color:#1B2530; }
  .toc .lyr { font-family:'IBM Plex Mono',monospace; font-size:8pt; color:#8B97A5;
              letter-spacing:.08em; margin-top:8pt; break-after:avoid; }
</style>
"""


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


def find_chrome():
    for c in CHROME_CANDIDATES:
        if os.path.exists(c):
            return c
    raise SystemExit("no headless Chrome/Edge found")


def build_toc(page):
    """Generate the contents list from the page's own nav."""
    nav = page[page.find('<nav class="side"'): page.find("</nav>")]
    items = []
    for m in re.finditer(
        r'<div class="grp-label">([^<]+)</div>|<a class="navlink"[^>]*>(.*?)</a>', nav
    ):
        if m.group(1):
            items.append(f'    <li class="lyr">{m.group(1).upper()}</li>')
        else:
            items.append(f"    <li>{m.group(2)}</li>")
    return "\n".join(items)


def title_block(cfg, label, toc):
    tp = cfg.get("title_page", {})
    lines = [f'  <h1>{tp.get("title", "")}</h1>']
    if tp.get("subtitle"):
        lines.append(f'  <p>{tp["subtitle"]}</p>')
    meta = " &middot; ".join(x for x in (tp.get("source", ""), label) if x)
    if meta:
        lines.append(f"  <p>{meta}</p>")
    if tp.get("note"):
        lines.append(f'  <p>{tp["note"]}</p>')
    body = "\n".join(lines)
    return f"""
<div class="titlepage">
{body}
</div>
<div class="toc">
  <h2>Contents</h2>
  <ul>
{toc}
  </ul>
</div>
"""


def main():
    ap = argparse.ArgumentParser(
        description="Render the built webpage into a single print-ready PDF manual."
    )
    ap.add_argument("--config", default=DEFAULT_CONFIG,
                    help="site config JSON (default: %(default)s)")
    ap.add_argument("--label", default=None,
                    help='edition label for the title page (default: config "pdf_label")')
    args = ap.parse_args()

    cfg = load_config(args.config)
    if "page" not in cfg or "pdf" not in cfg:
        raise SystemExit('config is missing required key: "page" or "pdf"')

    page_path = os.path.join(cfg["_dir"], cfg["page"])
    pdf_path = os.path.join(cfg["_dir"], cfg["pdf"])
    label = args.label if args.label is not None else cfg.get("pdf_label", "draft")

    page = open(page_path, encoding="utf-8").read()
    front = title_block(cfg, label, build_toc(page))

    # unhide every section, drop the SPA script, add print styling
    out = page.replace('" hidden>', '">')
    out = re.sub(r"<script>.*?</script>", "", out, flags=re.DOTALL)
    out = out.replace("</style>", "</style>\n" + PRINT_CSS, 1)
    out = out.replace('<div class="app">', front + '\n<div class="app">', 1)
    out = (
        '<!doctype html>\n<html lang="en" data-theme="light">\n<head>\n'
        '<meta charset="utf-8">\n' + out + "\n</body>\n</html>\n"
    )
    out = out.replace("</style>\n" + PRINT_CSS, "</style>\n" + PRINT_CSS + "\n</head>\n<body>", 1)

    stem = os.path.splitext(os.path.basename(pdf_path))[0]
    tmp = os.path.join(tempfile.gettempdir(), f"{stem}-print.html")
    open(tmp, "w", encoding="utf-8").write(out)

    subprocess.run(
        [
            find_chrome(), "--headless=new", "--disable-gpu", "--no-first-run",
            f"--print-to-pdf={pdf_path}", "--no-pdf-header-footer",
            "--virtual-time-budget=10000", f"file:///{tmp.replace(os.sep, '/')}",
        ],
        capture_output=True, timeout=180,
    )
    if not os.path.exists(pdf_path):
        raise SystemExit("PDF was not produced")
    print(f"wrote {os.path.basename(pdf_path)}: {os.path.getsize(pdf_path):,} bytes")

    site_pdf = os.path.join(cfg["_dir"], cfg.get("site_dir", "site"),
                            os.path.basename(pdf_path))
    if os.path.isdir(os.path.dirname(site_pdf)):
        shutil.copy2(pdf_path, site_pdf)


if __name__ == "__main__":
    main()
