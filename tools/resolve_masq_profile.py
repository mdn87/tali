#!/usr/bin/env python3
"""Locate a masq persona profile so it can serve as a tali voice spec.

masq is a separate Claude Code plugin, and its root is not derivable from
tali's CLAUDE_PLUGIN_ROOT, so this looks in the places an install actually
lands, in order:

  1. --root PATH, or the MASQ_PLUGIN_ROOT environment variable
  2. the install path recorded for masq in <plugins-dir>/installed_plugins.json
  3. <plugins-dir>/marketplaces/masq

and prints the path of profiles/<id>.md under the first root that has it.

Usage:
    python resolve_masq_profile.py dean [--plugins-dir ~/.claude/plugins] [--root PATH]

Exit status: 0 printed a path, 1 not found (the places searched are listed on
stderr), 2 bad arguments.
"""

import argparse
import json
import os
import sys


def candidate_roots(plugins_dir, explicit=None):
    roots = []
    for r in (explicit, os.environ.get("MASQ_PLUGIN_ROOT")):
        if r:
            roots.append(r)
    installed = os.path.join(plugins_dir, "installed_plugins.json")
    if os.path.isfile(installed):
        try:
            data = json.load(open(installed, encoding="utf-8"))
        except json.JSONDecodeError:
            data = {}
        for key, entries in data.get("plugins", {}).items():
            if key.split("@")[0] != "masq":
                continue
            for entry in entries if isinstance(entries, list) else [entries]:
                path = entry.get("installPath") if isinstance(entry, dict) else None
                if path:
                    roots.append(path)
    roots.append(os.path.join(plugins_dir, "marketplaces", "masq"))
    return roots


def resolve(profile_id, plugins_dir, explicit=None):
    """(profile path, roots searched); the path is None when nothing matched."""
    searched = []
    for root in candidate_roots(plugins_dir, explicit):
        path = os.path.join(root, "profiles", f"{profile_id}.md")
        searched.append(path)
        if os.path.isfile(path):
            return path, searched
    return None, searched


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("profile_id", help="masq profile id, the file name without .md")
    ap.add_argument("--plugins-dir", default=os.path.join(os.path.expanduser("~"), ".claude", "plugins"))
    ap.add_argument("--root", default=None, help="masq plugin root to try first")
    args = ap.parse_args(argv)
    if not args.profile_id or "/" in args.profile_id or "\\" in args.profile_id:
        print("error: profile id must be a bare name such as dean", file=sys.stderr)
        return 2

    path, searched = resolve(args.profile_id, args.plugins_dir, args.root)
    if path is None:
        print(f"masq profile {args.profile_id!r} not found; searched:", file=sys.stderr)
        for s in searched:
            print(f"  {s}", file=sys.stderr)
        return 1
    print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
