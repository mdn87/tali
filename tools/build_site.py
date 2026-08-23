#!/usr/bin/env python3
"""Assemble the deployable site: every prose version plus the version switcher.

For each entry in the config's "versions" list this writes one HTML file into
the site directory: the local page when "ref" is null, otherwise the page as
it exists at that git ref (commit or branch), so comparisons survive merges.
Each copy gets a switcher bar, an optional per-version cover swap, wide-table
marking, noindex/no-referrer meta, and a UTF-8 charset tag. Static assets
listed in the config are copied alongside. Run build_page.py first so the
local version reflects the current markdown.

Usage:  python build_site.py [--config tali.site.json]
"""

import argparse
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_page  # noqa: E402  (markdown -> HTML converter + config loader)

SWITCH_CSS = """
  /* version switcher */
  .vswitch { display:flex; gap:4px; padding:10px 16px 12px; border-bottom:1px solid var(--line);
             background:var(--surface); }
  .vsbtn { flex:1; text-align:center; font-family:'Public Sans',system-ui,sans-serif;
           font-size:11px; font-weight:600; letter-spacing:.01em; padding:7px 4px;
           border:1px solid var(--line); border-radius:6px; color:var(--muted);
           text-decoration:none; background:transparent; white-space:nowrap;
           transition:background .12s,color .12s; }
  .vsbtn:hover { background:var(--accent-wash); color:var(--accent-ink); }
  .vsbtn.active { background:var(--accent); border-color:var(--accent);
                  color:var(--on-accent); cursor:default; }
  .vsbtn.active:hover { background:var(--accent); color:var(--on-accent); }
"""

LAYOUT_CSS = """
  /* Text colour for use ON the accent fill. If the accent is dark in light
     mode and light in dark mode, a fixed white would lose contrast on dark.
     Both pairings below clear 7:1. */
  :root { --on-accent: #FFFFFF; }
  @media (prefers-color-scheme: dark) {
    :root:not([data-theme="light"]) { --on-accent: #0E1620; }
  }
  :root[data-theme="dark"] { --on-accent: #0E1620; }

  /* --- only wide tables leave the reading column -----------------------
     Four-plus column tables get a modest step up from the prose column,
     capped so rows stay trackable across. Narrower tables keep the
     reading width; dropping the per-cell min-width stops them scrolling
     sideways at any size. */
  .doc .tablewrap td { min-width: 0; }

  @media (min-width: 1000px) {
    .doc .tablewrap.wide {
      width: max(100%, min(54rem, calc(100vw - 27rem)));
      margin-left: 50%;
      transform: translateX(-50%);
    }
    .doc .tablewrap.wide table { font-size: .81rem; }
  }

  /* --- equation blocks (```equation fences in the markdown) ------------
     Reads as an actual equation: terms joined by operators, wrapping
     naturally. The terms are boxed because multi-word terms would
     otherwise run together across the plus signs. */
  .doc .equation {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: .4rem .45rem;
    margin: 1.2rem 0 1.45rem;
    padding: .95rem 1.05rem;
    background: var(--accent-wash);
    border-radius: 8px;
  }
  .doc .eqterm {
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 5px;
    padding: .3rem .62rem;
    font-family: 'Public Sans', system-ui, sans-serif;
    font-size: .845rem;
    line-height: 1.3;
    color: var(--ink);
    white-space: nowrap;
  }
  .doc .eqop {
    color: var(--accent);
    font-weight: 700;
    font-size: .95rem;
    padding: 0 .05rem;
  }
  .doc .eqsum {
    background: var(--accent);
    border: 1px solid var(--accent);
    border-radius: 5px;
    padding: .3rem .7rem;
    font-family: 'Public Sans', system-ui, sans-serif;
    font-size: .845rem;
    line-height: 1.3;
    font-weight: 700;
    color: var(--on-accent);
    white-space: nowrap;
  }
  @media (max-width: 560px) {
    .doc .eqterm, .doc .eqsum { white-space: normal; }
  }

  /* --- fill-in templates ({.form} tables in the markdown) --------------
     A form to read and complete, rather than a wall of monospace. */
  .doc .tablewrap.form table { font-size: .87rem; }
  .doc .tablewrap.form td { padding: .7rem .9rem; }
  .doc .tablewrap.form td:first-child {
    font-weight: 600; white-space: nowrap; width: 1%;
    color: var(--accent-ink); vertical-align: top;
  }
  .doc .tablewrap.form tr:nth-child(even) td { background: var(--accent-wash); }
  .doc .tablewrap.form td:last-child { color: var(--muted); }
"""

SWITCH_JS = """
<script>
(function () {
  var btns = document.querySelectorAll(".vsbtn");
  for (var i = 0; i < btns.length; i++) {
    btns[i].addEventListener("click", function (e) {
      if (this.classList.contains("active")) { e.preventDefault(); return; }
      this.href = this.getAttribute("data-href") + (location.hash || "");
    });
  }
})();
</script>
"""

NOINDEX = ('<meta name="robots" content="noindex, nofollow, noarchive, nosnippet">\n'
           '<meta name="referrer" content="no-referrer">')

# Must land inside the first 1024 bytes or browsers fall back to a legacy
# encoding and mangle every em-dash and middle dot. If the server sends
# Content-Type without a charset, this tag is what makes the page UTF-8.
CHARSET = '<meta charset="utf-8">'


def switcher(versions, active_key):
    rows = ['  <div class="vswitch" role="group" aria-label="Prose version">']
    for v in versions:
        cls = " active" if v["key"] == active_key else ""
        rows.append(
            f'    <a class="vsbtn{cls}" data-href="{v["url"]}" href="{v["url"]}">{v["label"]}</a>'
        )
    rows.append("  </div>\n")
    return "\n".join(rows)


def swap_cover(html_text, cfg, key):
    """Replace the landing section with this version's cover page."""
    covers = cfg.get("covers_dir")
    section = cfg.get("cover_section", "overview")
    if not covers:
        return html_text
    md_path = os.path.join(cfg["_dir"], covers, f"{section}-{key}.md")
    if not os.path.exists(md_path):
        return html_text

    md = open(md_path, encoding="utf-8").read()
    title_m = re.search(r"^#\s+(.*)$", md, re.M)
    title = build_page.inline(title_m.group(1)) if title_m else "Overview"
    body = build_page.convert(md, section)

    start = html_text.find(f'<section class="doc" id="doc-{section}"')
    if start == -1:
        return html_text
    end = html_text.find("</section>", start) + len("</section>")

    old = html_text[start:end]
    crumb_m = re.search(r"(<p class=\"crumb\">.*?</p>)", old, re.S)
    crumb = crumb_m.group(1) if crumb_m else ""

    new = (
        f'<section class="doc" id="doc-{section}" hidden>\n'
        f"  {crumb}\n"
        f"  <h1>{title}</h1>\n"
        f"  {body}\n"
        "</section>"
    )
    return html_text[:start] + new + html_text[end:]


def mark_wide_tables(html_text):
    """Tag tables with four or more columns so only those leave the reading
    column. Done here rather than at page-build time so the comparison
    versions, which come from older git refs, get it too."""

    def repl(m):
        block = m.group(0)
        if "tablewrap wide" in block or "tablewrap form" in block:
            return block
        first_row = re.search(r"<tr>(.*?)</tr>", block, re.S)
        cols = len(re.findall(r"<t[hd][\s>]", first_row.group(1))) if first_row else 0
        if cols >= 4:
            block = block.replace('class="tablewrap"', 'class="tablewrap wide"', 1)
        return block

    return re.sub(r'<div class="tablewrap[^"]*">.*?</table></div>', repl,
                  html_text, flags=re.S)


def prepare(html_text, cfg, version):
    key = version["key"]
    suffix = version.get("subtitle_suffix", "")

    html_text = swap_cover(html_text, cfg, key)
    html_text = mark_wide_tables(html_text)
    html_text = html_text.replace("</style>", SWITCH_CSS + LAYOUT_CSS + "</style>", 1)

    m = re.search(r'(<div class="brand">.*?</div>\s*\n)', html_text, re.S)
    if not m:
        raise SystemExit(f"{key}: could not find brand block")
    html_text = html_text[: m.end()] + switcher(cfg["versions"], key) + html_text[m.end():]

    if 'name="robots"' not in html_text:
        html_text = html_text.replace("</title>", "</title>\n" + NOINDEX, 1)

    if "charset" not in html_text[:1024].lower():
        html_text = CHARSET + "\n" + html_text

    if suffix:
        html_text = re.sub(
            r'(<div class="sub">)([^<]*)(</div>)',
            lambda mm: mm.group(1) + mm.group(2) + suffix + mm.group(3),
            html_text, count=1,
        )

    return html_text.rstrip() + "\n" + SWITCH_JS


def source_for(cfg, ref):
    if ref is None:
        page_path = os.path.join(cfg["_dir"], build_page.require(cfg, "page"))
        return open(page_path, encoding="utf-8").read()
    repo_rel = build_page.require(cfg, "page_repo_path")
    out = subprocess.run(
        ["git", "show", f"{ref}:{repo_rel}"],
        cwd=cfg["_dir"], capture_output=True, text=True, encoding="utf-8",
    ).stdout
    return out


def main():
    ap = argparse.ArgumentParser(
        description="Assemble the deployable multi-version site with a version switcher."
    )
    ap.add_argument("--config", default=build_page.DEFAULT_CONFIG,
                    help="site config JSON (default: %(default)s)")
    args = ap.parse_args()

    cfg = build_page.load_config(args.config)
    build_page.configure(cfg)

    site = os.path.join(cfg["_dir"], cfg.get("site_dir", "site"))
    os.makedirs(site, exist_ok=True)

    for version in build_page.require(cfg, "versions"):
        src = source_for(cfg, version.get("ref"))
        if not src.strip():
            print(f"  ! skipping {version['file']}: no content at ref {version.get('ref')}")
            continue
        open(os.path.join(site, version["file"]), "w", encoding="utf-8").write(
            prepare(src, cfg, version)
        )

    for extra in cfg.get("static_assets", []):
        s = os.path.join(cfg["_dir"], extra)
        if os.path.exists(s):
            shutil.copy2(s, os.path.join(site, os.path.basename(extra)))

    for f in sorted(os.listdir(site)):
        print(f"  {f:36} {os.path.getsize(os.path.join(site, f)):>9,} bytes")


if __name__ == "__main__":
    main()
