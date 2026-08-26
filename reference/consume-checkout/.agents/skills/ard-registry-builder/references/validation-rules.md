# Validation Rules Reference

This is the complete catalogue of checks `scripts/validate_catalog.py` performs, with the
stable `code` each finding carries (visible in `--json` output). Two layers run:

1. **Schema** — full JSON Schema Draft 2020-12 validation against
   `assets/ai-catalog.schema.json` (via the `jsonschema` library; a built-in structural
   checker is used as a fallback when the library is absent). All schema findings use code
   `schema`.
2. **Semantic** — ARD rules the schema cannot express, each with its own code below.

Severity model: **ERROR** blocks (exit 1). **WARN** is advisory (exit 0, unless `--strict`).
**INFO** is a suggestion. Run with `--strict` in CI to also fail on warnings.

## ERROR-level

| code | Rule |
| :-- | :-- |
| `schema` | Any structural violation: missing `specVersion`/`entries`/`identifier`/`displayName`/`type`, wrong types, `representativeQueries` not 2–5, attestation missing `type`/`uri`/`mediaType`, unknown keys where `additionalProperties:false`, etc. |
| `urn-wrong-nid` | `identifier` starts with `urn:ai:` instead of `urn:air:`. The NID is `air`; `urn:ai:` (seen in some docs) is incorrect. |
| `urn-format` | `identifier` does not match `^urn:air:[a-zA-Z0-9.-]+(:[a-zA-Z0-9._-]+)+$`. |
| `value-or-reference` | Entry has **both** `url` and `data`, or **neither**. Exactly one is required (ARD §3.4). |
| `duplicate-identifier` | Two entries share an `identifier`. Identifiers are the discovery primary key and must be unique within a catalog. |

## WARN-level

| code | Rule |
| :-- | :-- |
| `urn-localhost` | URN publisher is bare `localhost` — not globally unique or verifiable. Use `agent.localhost` or `example.com` for local dev. |
| `urn-publisher-fqdn` | URN publisher has no dot, so it is not a FQDN. Trust is anchored in DNS; the publisher should be a real or reserved domain. |
| `url-not-https` | `url` is plain `http://` to a non-local host. Published manifests must be served over HTTPS. |
| `type-not-media-type` | `type` is not an IANA media type (no `/`). |
| `updatedat-format` | `updatedAt` is not a parseable ISO 8601 / date-time value. |
| `trust-domain-mismatch` | The domain inside `trustManifest.identity` (SPIFFE/`did:web`/HTTPS) does not align with the URN publisher, so a registry cannot bind the identity to the publisher. |
| `schema-missing` | The bundled schema could not be loaded; only semantic checks ran. |

## INFO-level

| code | Rule |
| :-- | :-- |
| `missing-representative-queries` | An agent/server entry has no `representativeQueries`. Adding 2–5 sample queries greatly improves semantic discoverability. |
| `urn-no-namespace` | `identifier` has no `<namespace>` segment between publisher and agent-name. Allowed, but namespaces help organize larger catalogs. |

## Nested sub-catalogs
When an entry has inline `data` and a `type` containing `ai-catalog`, the validator recurses
into the embedded manifest, reporting findings with a path like
`entries[2].data.entries[0]....`. This validates bundles published as a single document.

## Usage
```bash
# Local file or live URL
python scripts/validate_catalog.py ./ai-catalog.json
python scripts/validate_catalog.py https://example.com/.well-known/ai-catalog.json

# Machine-readable output for CI; non-zero exit on errors
python scripts/validate_catalog.py ./ai-catalog.json --json

# Fail the build on warnings too
python scripts/validate_catalog.py ./ai-catalog.json --strict
```

## Cross-checking with AJV (optional)
The spec also documents validation with the JavaScript AJV CLI, which is handy as an
independent second opinion on pure schema conformance:
```bash
npx ajv-cli validate -s assets/ai-catalog.schema.json -d ./ai-catalog.json
```
AJV checks structure only; it does not perform the ARD semantic checks above.

## Cross-checking against the official conformance tool (optional)
The ARD spec repo ships an official, zero-dependency conformance CLI written in Python that
this validator deliberately mirrors — the same two layers (`jsonschema` structural checks plus
ARD semantic checks such as URN formatting, Strict Value-or-Reference, and
`representativeQueries` sizing). To cross-check a manifest against the canonical reference:
```bash
./conformance/bin/conformance-test manifest ./ai-catalog.json
./conformance/bin/conformance-test manifest https://example.com/.well-known/ai-catalog.json
```
Because it applies the same rule set, treat a pass as a conformance confirmation, not an
independent engine — use AJV above when you want a structurally independent second opinion.
