#!/usr/bin/env python3
"""Scaffold a starter ARD ai-catalog.json manifest from a bundled template.

Copies one of the built-in templates (minimal | enterprise | local-dev) and,
optionally, rewrites the example publisher domain and host name so the result is
a ready-to-edit manifest for your own domain. Always re-run validate_catalog.py
after editing.

Usage:
    python new_catalog.py --template minimal --out ./ai-catalog.json
    python new_catalog.py --template enterprise --publisher mycorp.com \
        --host "MyCorp AI" --out ./.well-known/ai-catalog.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "assets" / "templates"
EXAMPLE_DOMAINS = ("acme.com", "agent.localhost", "example.com")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Scaffold an ARD ai-catalog.json from a template.")
    ap.add_argument("--template", choices=["minimal", "enterprise", "local-dev"], default="minimal")
    ap.add_argument("--out", default="ai-catalog.json", help="Output path for the new manifest.")
    ap.add_argument("--publisher", help="Replace the example publisher domain in URN identifiers (e.g. mycorp.com).")
    ap.add_argument("--host", help="Override host.displayName.")
    ap.add_argument("--force", action="store_true", help="Overwrite the output file if it exists.")
    args = ap.parse_args(argv)

    src = TEMPLATES_DIR / f"{args.template}.json"
    text = src.read_text(encoding="utf-8")

    if args.publisher:
        # Only rewrite the publisher inside urn:air:<publisher>: occurrences, keeping URLs untouched.
        for dom in EXAMPLE_DOMAINS:
            text = text.replace(f"urn:air:{dom}:", f"urn:air:{args.publisher}:")

    doc = json.loads(text)
    if args.host:
        doc.setdefault("host", {})["displayName"] = args.host

    out = Path(args.out)
    if out.exists() and not args.force:
        print(f"refusing to overwrite existing {out} (use --force)")
        return 1
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")

    print(f"Wrote {args.template} manifest to {out}")
    print("Next: edit identifiers/urls, then validate with:")
    print(f"  python {Path(__file__).parent / 'validate_catalog.py'} {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
