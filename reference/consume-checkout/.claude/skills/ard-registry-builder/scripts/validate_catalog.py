#!/usr/bin/env python3
"""Validate an ARD ai-catalog.json capability manifest.

Runs two layers of checks:
  1. Structural JSON Schema validation against the authoritative
     ai-catalog.schema.json (Draft 2020-12). Uses the `jsonschema` library when
     available; otherwise falls back to a built-in structural checker.
  2. ARD semantic checks that the JSON Schema cannot express on its own - URN
     identity rules, Strict Value-or-Reference, trust-domain alignment, HTTPS
     hygiene, duplicate identifiers, and common copy-paste mistakes.

Source may be a local path or an http(s) URL (e.g. a live /.well-known/ai-catalog.json).

Exit codes: 0 = passed, 1 = errors found (or warnings in --strict), 2 = usage/load error.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "assets" / "ai-catalog.schema.json"

URN_RE = re.compile(r"^urn:air:[a-zA-Z0-9.-]+(:[a-zA-Z0-9._-]+)+$")
ERROR, WARN, INFO = "ERROR", "WARN", "INFO"


class Finding:
    __slots__ = ("level", "path", "code", "message")

    def __init__(self, level: str, path: str, code: str, message: str):
        self.level, self.path, self.code, self.message = level, path, code, message

    def as_dict(self) -> dict:
        return {"level": self.level, "path": self.path, "code": self.code, "message": self.message}


class Report:
    def __init__(self) -> None:
        self.findings: list[Finding] = []

    def add(self, level: str, path: str, code: str, message: str) -> None:
        self.findings.append(Finding(level, path, code, message))

    def count(self, level: str) -> int:
        return sum(1 for f in self.findings if f.level == level)

    @property
    def ok(self) -> bool:
        return self.count(ERROR) == 0


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #
def load_source(source: str) -> tuple[dict, str]:
    """Return (parsed_json, origin_label). Raises ValueError on failure."""
    if re.match(r"^https?://", source):
        req = urllib.request.Request(source, headers={"User-Agent": "ard-registry-builder/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                raw = resp.read().decode("utf-8")
        except Exception as exc:  # noqa: BLE001
            raise ValueError(f"could not fetch {source}: {exc}") from exc
        label = source
    else:
        p = Path(source)
        if not p.is_file():
            raise ValueError(f"file not found: {source}")
        raw = p.read_text(encoding="utf-8")
        label = str(p)
    try:
        return json.loads(raw), label
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {label}: {exc}") from exc


def load_schema() -> dict | None:
    try:
        return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None


# --------------------------------------------------------------------------- #
# Layer 1: JSON Schema
# --------------------------------------------------------------------------- #
def run_schema_validation(doc, schema: dict | None, report: Report) -> str:
    """Returns a label describing which validator was used."""
    if schema is None:
        report.add(WARN, "$schema", "schema-missing",
                   "bundled ai-catalog.schema.json could not be loaded; ran semantic checks only")
        return "none"
    try:
        import jsonschema  # type: ignore
        from jsonschema import Draft202012Validator
    except ImportError:
        _fallback_structural(doc, report)
        return "built-in fallback (install 'jsonschema' for full Draft 2020-12 checks)"

    validator = Draft202012Validator(schema)
    for err in sorted(validator.iter_errors(doc), key=lambda e: list(e.absolute_path)):
        # The only oneOf in the schema is the url-vs-data constraint; jsonschema reports it by
        # dumping the entire entry. The semantic layer reports it far more clearly (both vs neither),
        # so skip the noisy schema variant to avoid duplicate, unreadable output.
        if err.validator == "oneOf":
            continue
        path = _ptr(err.absolute_path)
        report.add(ERROR, path, "schema", err.message)
    return "jsonschema (Draft 2020-12)"


def _ptr(absolute_path) -> str:
    parts = list(absolute_path)
    if not parts:
        return "(root)"
    out = ""
    for part in parts:
        if isinstance(part, int):
            out += f"[{part}]"
        else:
            out += f".{part}" if out else str(part)
    return out


def _fallback_structural(doc, report: Report) -> None:
    """Minimal structural checks when jsonschema is not installed."""
    if not isinstance(doc, dict):
        report.add(ERROR, "(root)", "schema", "manifest must be a JSON object")
        return
    if doc.get("specVersion") != "1.0":
        report.add(ERROR, "specVersion", "schema", "specVersion is required and must equal \"1.0\"")
    entries = doc.get("entries")
    if not isinstance(entries, list):
        report.add(ERROR, "entries", "schema", "entries is required and must be an array")
        return
    host = doc.get("host")
    if isinstance(host, dict) and not isinstance(host.get("displayName"), str):
        report.add(ERROR, "host.displayName", "schema", "host.displayName is required when host is present")
    for i, entry in enumerate(entries):
        base = f"entries[{i}]"
        if not isinstance(entry, dict):
            report.add(ERROR, base, "schema", "entry must be an object")
            continue
        for field in ("identifier", "displayName", "type"):
            if not isinstance(entry.get(field), str):
                report.add(ERROR, f"{base}.{field}", "schema", f"{field} is required and must be a string")
        rq = entry.get("representativeQueries")
        if isinstance(rq, list) and not (2 <= len(rq) <= 5):
            report.add(ERROR, f"{base}.representativeQueries", "schema",
                       "representativeQueries must contain between 2 and 5 items")
        tm = entry.get("trustManifest")
        if isinstance(tm, dict):
            if not isinstance(tm.get("identity"), str):
                report.add(ERROR, f"{base}.trustManifest.identity", "schema", "trustManifest.identity is required")
            for j, att in enumerate(tm.get("attestations", []) or []):
                if isinstance(att, dict):
                    for field in ("type", "uri", "mediaType"):
                        if field not in att:
                            report.add(ERROR, f"{base}.trustManifest.attestations[{j}].{field}", "schema",
                                       f"attestation.{field} is required")


# --------------------------------------------------------------------------- #
# Layer 2: ARD semantic checks
# --------------------------------------------------------------------------- #
def domain_of_identity(identity: str) -> str | None:
    if not isinstance(identity, str):
        return None
    if identity.startswith("spiffe://"):
        return identity[len("spiffe://"):].split("/", 1)[0] or None
    if identity.startswith("did:web:"):
        # did:web:example.com  or  did:web:example.com:path (':' separates path)
        return identity[len("did:web:"):].split(":", 1)[0] or None
    if identity.startswith(("https://", "http://")):
        return urlparse(identity).hostname
    return None


def domains_aligned(publisher: str, identity_domain: str) -> bool:
    p, d = publisher.lower().rstrip("."), identity_domain.lower().rstrip(".")
    return p == d or p.endswith("." + d) or d.endswith("." + p)


def check_entry(entry: dict, base: str, report: Report) -> None:
    identifier = entry.get("identifier")

    # --- URN identity rules ---
    if isinstance(identifier, str):
        if identifier.startswith("urn:ai:") and not identifier.startswith("urn:air:"):
            report.add(ERROR, f"{base}.identifier", "urn-wrong-nid",
                       "identifier uses 'urn:ai:' but the authoritative schema requires 'urn:air:' "
                       "(NID 'air' = Agentic Resource discovery). Some older docs show 'urn:ai:' - that is incorrect.")
        elif not URN_RE.match(identifier):
            report.add(ERROR, f"{base}.identifier", "urn-format",
                       "identifier must match urn:air:<publisher>:<namespace?>:<agent-name> "
                       "(pattern ^urn:air:[a-zA-Z0-9.-]+(:[a-zA-Z0-9._-]+)+$)")
        else:
            segments = identifier.split(":")  # urn, air, publisher, ...rest
            publisher = segments[2]
            if publisher == "localhost":
                report.add(WARN, f"{base}.identifier", "urn-localhost",
                           "publisher 'localhost' is an anti-pattern: it is not globally unique or verifiable. "
                           "Use a placeholder FQDN such as 'agent.localhost' or 'example.com' for local dev.")
            elif "." not in publisher:
                report.add(WARN, f"{base}.identifier", "urn-publisher-fqdn",
                           f"publisher '{publisher}' is not a fully qualified domain name. The publisher segment "
                           "should be a verifiable FQDN (e.g. acme.com, github.com) so trust can be anchored in DNS.")
            if len(segments) < 5:
                report.add(INFO, f"{base}.identifier", "urn-no-namespace",
                           "identifier has no <namespace> segment between publisher and agent-name. This is allowed, "
                           "but namespaces (e.g. finance:trading) help organize larger catalogs.")

    # --- Strict Value-or-Reference ---
    has_url, has_data = "url" in entry, "data" in entry
    if has_url and has_data:
        report.add(ERROR, base, "value-or-reference",
                   "entry contains BOTH 'url' and 'data'; exactly one is allowed (ARD sec 3.4 Strict Value-or-Reference).")
    elif not has_url and not has_data:
        report.add(ERROR, base, "value-or-reference",
                   "entry contains NEITHER 'url' nor 'data'; exactly one is required (ARD sec 3.4).")

    # --- url hygiene ---
    url = entry.get("url")
    if isinstance(url, str):
        host = urlparse(url).hostname or ""
        if url.startswith("http://") and host not in ("localhost", "127.0.0.1", "::1"):
            report.add(WARN, f"{base}.url", "url-not-https",
                       "url is plain http://. Published manifests must be served over HTTPS; "
                       "http is acceptable only for local development endpoints.")

    # --- type / media-type ---
    mtype = entry.get("type")
    if isinstance(mtype, str) and "/" not in mtype:
        report.add(WARN, f"{base}.type", "type-not-media-type",
                   f"type '{mtype}' is not an IANA media type. Expected something like "
                   "application/mcp-server-card+json, application/a2a-agent-card+json, or application/ai-skill.")

    # --- representativeQueries advice ---
    if "representativeQueries" not in entry and isinstance(mtype, str) and (
        "agent-card" in mtype or "mcp-server" in mtype
    ):
        report.add(INFO, base, "missing-representative-queries",
                   "no representativeQueries. Registries use 2-5 sample queries to build semantic search ranking; "
                   "adding them greatly improves how discoverable this entry is.")

    # --- updatedAt parse ---
    updated = entry.get("updatedAt")
    if isinstance(updated, str):
        iso = updated.replace("Z", "+00:00")
        try:
            datetime.fromisoformat(iso)
        except ValueError:
            report.add(WARN, f"{base}.updatedAt", "updatedat-format",
                       f"updatedAt '{updated}' is not a parseable ISO 8601 / date-time value.")

    # --- trust-domain alignment ---
    tm = entry.get("trustManifest")
    if isinstance(tm, dict) and isinstance(identifier, str) and URN_RE.match(identifier):
        publisher = identifier.split(":")[2]
        idomain = domain_of_identity(tm.get("identity", ""))
        if idomain and not domains_aligned(publisher, idomain):
            report.add(WARN, f"{base}.trustManifest.identity", "trust-domain-mismatch",
                       f"trustManifest identity domain '{idomain}' does not align with the URN publisher "
                       f"'{publisher}'. The authority domain in the identity SHOULD match the publisher so a "
                       "registry can verify the publisher actually controls this identity.")


def check_manifest(doc, report: Report, base: str = "") -> None:
    if not isinstance(doc, dict):
        return
    entries = doc.get("entries")
    if isinstance(entries, list):
        if not entries:
            report.add(WARN, f"{base}entries" if base else "entries", "empty-entries",
                       "entries is empty. A catalog SHOULD advertise at least one agentic resource.")
        seen: dict[str, int] = {}
        for i, entry in enumerate(entries):
            ebase = f"{base}entries[{i}]"
            if not isinstance(entry, dict):
                continue
            ident = entry.get("identifier")
            if isinstance(ident, str):
                if ident in seen:
                    report.add(ERROR, f"{ebase}.identifier", "duplicate-identifier",
                               f"duplicate identifier '{ident}' (also at entries[{seen[ident]}]). "
                               "Identifiers are the primary key for discovery and MUST be unique within a catalog.")
                else:
                    seen[ident] = i
            check_entry(entry, ebase, report)
            # Recurse into embedded sub-catalogs (application/ai-catalog+json with inline data).
            data = entry.get("data")
            mtype = entry.get("type", "")
            if isinstance(data, dict) and isinstance(mtype, str) and "ai-catalog" in mtype:
                check_manifest(data, report, base=f"{ebase}.data.")


# --------------------------------------------------------------------------- #
# Output
# --------------------------------------------------------------------------- #
LEVEL_ORDER = {ERROR: 0, WARN: 1, INFO: 2}


def print_human(report: Report, source: str, validator_label: str, strict: bool) -> None:
    print(f"ARD catalog validation: {source}")
    print(f"Schema validation: {validator_label}\n")
    if not report.findings:
        print("No issues found.")
    for f in sorted(report.findings, key=lambda x: (LEVEL_ORDER[x.level], x.path)):
        print(f"{f.level:<5} {f.path}: {f.message}")
    e, w, i = report.count(ERROR), report.count(WARN), report.count(INFO)
    failed = e > 0 or (strict and w > 0)
    verdict = "FAIL" if failed else "PASS"
    suffix = " (--strict: warnings treated as errors)" if strict and w and e == 0 else ""
    print(f"\nResult: {verdict} - {e} error(s), {w} warning(s), {i} info{suffix}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Validate an ARD ai-catalog.json manifest.")
    ap.add_argument("source", help="Path or http(s) URL to an ai-catalog.json manifest.")
    ap.add_argument("--json", action="store_true", help="Emit findings as JSON.")
    ap.add_argument("--strict", action="store_true", help="Treat warnings as failures.")
    args = ap.parse_args(argv)

    try:
        doc, label = load_source(args.source)
    except ValueError as exc:
        if args.json:
            print(json.dumps({"source": args.source, "ok": False, "error": str(exc)}, indent=2))
        else:
            print(f"ERROR  could not load manifest: {exc}", file=sys.stderr)
        return 2

    report = Report()
    validator_label = run_schema_validation(doc, load_schema(), report)
    check_manifest(doc, report)

    failed = not report.ok or (args.strict and report.count(WARN) > 0)
    if args.json:
        print(json.dumps({
            "source": label,
            "schema_validator": validator_label,
            "ok": not failed,
            "counts": {"error": report.count(ERROR), "warning": report.count(WARN), "info": report.count(INFO)},
            "findings": [f.as_dict() for f in report.findings],
        }, indent=2))
    else:
        print_human(report, label, validator_label, args.strict)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
