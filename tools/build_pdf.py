#!/usr/bin/env python3
"""Render the built webpage into a single print-ready PDF manual.

Unhides every section, strips the single-page-app JS, adds print styling,
and generates the title page and contents from the page's own nav so the
manual can never drift from the site. Rendering uses headless Chrome, Edge,
or Chromium, found on the usual paths for Windows, macOS, and Linux, on PATH,
or given explicitly. The page filename, PDF filename, title-page text, and
default edition label all come from the JSON site config; if the config's
site directory exists, the PDF is copied there too.

Usage:
    python build_pdf.py [--config tali.site.json] [--label "draft 2026-08-23"]
    python build_pdf.py --page site/casual.html --pdf handbook-casual.pdf   # one voice
    python build_pdf.py --chrome "/path/to/chrome"      # or set TALI_CHROME

Exit status: 0 ok, 1 the browser did not produce a PDF, 2 config error.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_page import DEFAULT_CONFIG, ConfigError, load_config, require  # noqa: E402

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Google\Chrome\Application\chrome.exe"),
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/usr/bin/google-chrome",
    "/usr/bin/google-chrome-stable",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
    "/usr/bin/microsoft-edge",
    "/snap/bin/chromium",
]
CHROME_NAMES = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser",
                "chrome", "msedge", "microsoft-edge"]

PRINT_CSS = """
<style>
  html, body { background:#FFFFFF; }
  .side, .pager, #pager, .vswitch { display:none !important; }
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


def find_chrome(explicit=None):
    """The browser binary: explicit flag, TALI_CHROME, known paths, then PATH."""
    for c in (explicit, os.environ.get("TALI_CHROME")):
        if c:
            if os.path.exists(c) or shutil.which(c):
                return c
            raise ConfigError(f"browser not found: {c}")
    for c in CHROME_CANDIDATES:
        if c and os.path.exists(c):
            return c
    for name in CHROME_NAMES:
        found = shutil.which(name)
        if found:
            return found
    raise ConfigError(
        "no headless Chrome, Edge, or Chromium found; install one, put it on PATH, "
        "pass --chrome PATH, or set TALI_CHROME"
    )


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


def print_html(page, cfg, label):
    """The page rewritten for print: every section shown, no SPA script,
    print CSS, and the generated title page and contents up front."""
    front = title_block(cfg, label, build_toc(page))

    out = page.replace('" hidden>', '">')
    out = re.sub(r"<script>.*?</script>", "", out, flags=re.DOTALL)
    if "</style>" in out:
        out = out.replace("</style>", "</style>\n" + PRINT_CSS, 1)
    else:
        out = re.sub(r"</head>", PRINT_CSS + "\n</head>", out, count=1, flags=re.I)
    if '<div class="app">' in out:
        out = out.replace('<div class="app">', front + '\n<div class="app">', 1)
    else:
        out = re.sub(r"(<body[^>]*>)", lambda m: m.group(1) + front, out, count=1, flags=re.I)

    if re.search(r"<html", out, re.I):
        # a full document: force the light theme for print, leave the rest
        out = re.sub(
            r"<html(?![^>]*data-theme)", '<html data-theme="light"', out, count=1, flags=re.I
        )
        return out

    # a fragment that starts at <title>/<style>: wrap it into a document
    out = (
        '<!doctype html>\n<html lang="en" data-theme="light">\n<head>\n'
        '<meta charset="utf-8">\n' + out + "\n</body>\n</html>\n"
    )
    return out.replace("</style>\n" + PRINT_CSS, "</style>\n" + PRINT_CSS + "\n</head>\n<body>", 1)


def render(html_path, pdf_path, chrome):
    """Run the browser headless. Returns the stderr text when no PDF appears."""
    proc = subprocess.run(
        [
            chrome, "--headless=new", "--disable-gpu", "--no-first-run", "--no-sandbox",
            f"--print-to-pdf={pdf_path}", "--no-pdf-header-footer",
            "--virtual-time-budget=10000", f"file:///{html_path.replace(os.sep, '/')}",
        ],
        capture_output=True, text=True, errors="replace", timeout=180,
    )
    if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
        return ""
    tail = "\n".join(proc.stderr.strip().splitlines()[-5:])
    return f"browser exited {proc.returncode}\n{tail}".strip()


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Render the built webpage into a single print-ready PDF manual."
    )
    ap.add_argument("--config", default=DEFAULT_CONFIG,
                    help="site config JSON (default: %(default)s)")
    ap.add_argument("--label", default=None,
                    help='edition label for the title page (default: config "pdf_label")')
    ap.add_argument("--page", default=None,
                    help="HTML file to render instead of the config's page, e.g. site/casual.html")
    ap.add_argument("--pdf", default=None,
                    help="output PDF path instead of the config's pdf")
    ap.add_argument("--chrome", default=None,
                    help="browser binary (default: known paths, PATH, or $TALI_CHROME)")
    args = ap.parse_args(argv)

    try:
        cfg = load_config(args.config)
        page_path = os.path.join(cfg["_dir"], args.page or require(cfg, "page"))
        pdf_path = os.path.join(cfg["_dir"], args.pdf or require(cfg, "pdf"))
        if not os.path.isfile(page_path):
            raise ConfigError(f"page not found: {page_path}")
        chrome = find_chrome(args.chrome)
    except ConfigError as e:
        print(f"config error: {e}", file=sys.stderr)
        return 2

    label = args.label if args.label is not None else cfg.get("pdf_label", "draft")
    page = open(page_path, encoding="utf-8").read()
    out = print_html(page, cfg, label)

    stem = os.path.splitext(os.path.basename(pdf_path))[0]
    tmp = os.path.join(tempfile.gettempdir(), f"{stem}-print.html")
    open(tmp, "w", encoding="utf-8").write(out)

    if os.path.exists(pdf_path):
        os.remove(pdf_path)
    failure = render(tmp, pdf_path, chrome)
    if failure:
        print(f"PDF was not produced: {failure}", file=sys.stderr)
        return 1
    print(f"wrote {os.path.basename(pdf_path)}: {os.path.getsize(pdf_path):,} bytes")

    site_pdf = os.path.join(cfg["_dir"], cfg.get("site_dir", "site"),
                            os.path.basename(pdf_path))
    if os.path.isdir(os.path.dirname(site_pdf)) and os.path.abspath(site_pdf) != os.path.abspath(pdf_path):
        shutil.copy2(pdf_path, site_pdf)
    return 0


if __name__ == "__main__":
    sys.exit(main())
