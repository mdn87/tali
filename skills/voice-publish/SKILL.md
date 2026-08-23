---
name: voice-publish
description: This skill should be used when the user wants to publish a multi-voice document set as a comparison website or PDF manual — for example "build the voice site", "regenerate the handbook PDF", "publish the voice comparison", or "rebuild the page from markdown".
---

# Voice Publish

Publish a set of markdown documents as a single-page comparison website (one
HTML file per prose voice, joined by a version switcher) and a print-ready PDF
manual. Three stdlib-only Python scripts do the work, all driven by one JSON
config, `tali.site.json`.

**Script paths.** When this skill runs from the installed plugin, invoke the
scripts as `${CLAUDE_PLUGIN_ROOT}/tools/build_page.py`,
`${CLAUDE_PLUGIN_ROOT}/tools/build_site.py`, and
`${CLAUDE_PLUGIN_ROOT}/tools/build_pdf.py`. If the scripts have been vendored
into the project (copied into, say, `tools/`), use plain relative paths
instead. Every script accepts `--config PATH` and defaults to
`./tali.site.json` in the current directory.

## Setting up tali.site.json for a project

Start from `${CLAUDE_PLUGIN_ROOT}/tools/tali.site.example.json` — copy it next
to the page HTML as `tali.site.json` and edit. Keys beginning with `_` are
comments and ignored; all paths are relative to the config file's directory.
The fields:

- `page` — the single-page HTML shell. It must already exist, with
  `<section class="doc" id="doc-<id>">` blocks for each document, a
  `<div class="brand">` header, a `<div class="sub">` subtitle, and a
  `<nav class="side">` nav (the PDF contents are generated from it).
- `sources_root` — root directory of the markdown sources.
- `section_sources` — map of section id → markdown file under `sources_root`.
  Sections in the page that are not listed are preserved untouched (hand-built
  reference sections survive rebuilds).
- `link_map` — markdown link basename → in-page anchor, so cross-references
  between source files become in-page links. Unmapped local links are dropped
  (label kept); URLs and `#anchors` pass through.
- `chips` — optional list of `{label, class}` pairs; a paragraph beginning
  with `**label**` becomes `<span class="chip <class>">`. The page CSS must
  define the chip classes.
- `skip_prefixes` — optional list of line prefixes to drop (frontmatter-style
  metadata lines).
- `site_dir`, `covers_dir`, `cover_section` — site output directory, and the
  optional per-version cover swap: `covers_dir/<cover_section>-<key>.md`
  replaces the cover section body for that version.
- `page_repo_path`, `versions` — see the versioning pattern below.
- `static_assets` — files copied into `site_dir` when present (robots.txt,
  headers file, the PDF).
- `pdf`, `pdf_label`, `title_page` — PDF filename, default edition label, and
  title-page text (`title`, `subtitle`, `source`, `note`).

## The three-script workflow

Run from the config's directory (or pass `--config` explicitly), in order:

1. `python build_page.py` — regenerates the mapped sections of `page` in
   place from the markdown sources, preserving the shell (CSS, nav, JS) and
   unmapped sections. **Run `build_page.py --check` first** — it reports how
   many sections would change without writing, and catches config or source
   problems before anything is modified.
2. `python build_site.py` — assembles `site_dir`: one prepared HTML file per
   version (switcher bar, cover swap, wide-table marking, noindex, UTF-8
   charset tag) plus the static assets. Run build_page first so the local
   version reflects current markdown.
3. `python build_pdf.py [--label "draft 2026-08-23 · <commit>"]` — renders
   the page into a print-ready PDF via headless Chrome/Edge: all sections
   unhidden, SPA script stripped, auto title page and table of contents from
   the page nav. The label defaults to `pdf_label`; pass `--label` to stamp a
   date or commit. The PDF is copied into `site_dir` if it exists.

On Windows use `py -3` in place of `python`. Python 3.12+, stdlib only.

## Git-ref versioning pattern

Each entry in `versions` has a `ref`:

- `null` — build from the local `page` file (the current working tree). This
  is normally the index/default voice.
- **A commit hash** — pin the *original* prose to the commit made just before
  the first voice pass. It can never drift, even after the history moves on.
- **A branch name** — keep each persona/voice variant on its own branch
  (e.g. `voice-casual`) and reference the branch. The comparison keeps
  working after the main branch merges, because `git show <branch>:<path>`
  reads the branch tip, not the merge result.

`page_repo_path` is the repo-relative path of the page file, used for
`git show <ref>:<page_repo_path>`. A version whose ref yields no content is
skipped with a warning rather than failing the build.

## Deployment

The output is a plain static directory (`site_dir`) — any static host works
(GitHub Pages, Netlify, nginx, S3). One worked option is a Cloudflare Worker
with static assets: put a `wrangler.jsonc` next to the config like

```jsonc
{
  "name": "handbook",
  "compatibility_date": "2026-08-23",
  "assets": {
    "directory": "./site",
    "not_found_handling": "single-page-application"
  },
  "routes": [
    { "pattern": "docs.example.com", "custom_domain": true }
  ]
}
```

and deploy with `npx wrangler deploy` from that directory. The
`single-page-application` fallback keeps deep links to `/casual` or
`/original` working. Remember that the noindex/no-referrer meta tags are
injected by build_site; if the host also serves headers, a `_headers` file in
`static_assets` can duplicate them at the HTTP layer.
