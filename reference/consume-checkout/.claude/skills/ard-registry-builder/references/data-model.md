# ARD Data Model — `ai-catalog.json` capability manifest

The authoritative machine-readable schema is bundled at
`assets/ai-catalog.schema.json` (JSON Schema Draft 2020-12). This file explains it in
prose. When prose and schema disagree, **the schema wins** — and the bundled validator
enforces the schema.

## Table of contents
- [Mental model: identity vs location](#mental-model-identity-vs-location)
- [Manifest structure](#manifest-structure)
- [Catalog entry](#catalog-entry)
- [The URN identifier](#the-urn-identifier)
- [Media types (the `type` field)](#media-types-the-type-field)
- [Strict Value-or-Reference](#strict-value-or-reference)
- [Trust manifest](#trust-manifest)
- [Known doc inconsistencies](#known-doc-inconsistencies)

## Mental model: identity vs location
ARD separates **what a resource *is*** (its permanent logical identity, the `identifier`
URN) from **where it *lives*** (its physical endpoint, `url` or inline `data`). The URN is
a stable contract; the endpoint can move freely without breaking discovery, indexing, or
orchestration. Keep this split in mind for every decision: never bake a hostname into a URN,
never treat a URL as an identity.

## Manifest structure
A publisher hosts one JSON document, conventionally at
`https://<domain>/.well-known/ai-catalog.json`.

| Field | Required | Notes |
| :-- | :-- | :-- |
| `specVersion` | yes | Must be the string `"1.0"`. |
| `host` | no | Describes the operator (see below). |
| `entries` | yes | Array of catalog entries. The spec expects at least one (the validator warns on empty). |

`host` object: `displayName` (required when `host` is present), optional `identifier`
(a verifiable id such as `did:web:acme.com`), `documentationUrl`, `logoUrl`, `trustManifest`.
`additionalProperties` is **false** at the manifest and host levels — unknown keys fail validation.

## Catalog entry
Each entry advertises one agentic resource (an MCP server, A2A agent, skill, dataset, API,
sub-catalog, or registry).

Required: `identifier`, `displayName`, `type`, **and exactly one of** `url` or `data`.

Optional: `description`, `tags` (array), `capabilities` (array of skill/tool names for fast
filtering), `representativeQueries` (2–5 natural-language samples used to build semantic search
ranking), `version`, `updatedAt` (ISO 8601 date-time), `metadata` (map of scalar values),
`trustManifest`.

`representativeQueries` is the single highest-leverage optional field for discoverability:
registries embed these 2–5 phrases to match user intent. Add them to anything you want found.

## The URN identifier
Format (RFC 8141): `urn:air:<publisher>:<namespace?>:<agent-name>`

- `urn:air:` — fixed prefix. The NID is **`air`** (Agentic Resource discovery), not `ai`.
- `<publisher>` — a verifiable FQDN (e.g. `acme.com`, `github.com`, `hf.co`). This is the
  trust anchor: registries extract it and cross-check it against `trustManifest.identity`.
- `<namespace>` — optional, one or more `:`-separated segments (e.g. `finance:trading`).
- `<agent-name>` — the terminal short name (e.g. `assistant`, `tax-agent`).

Schema pattern: `^urn:air:[a-zA-Z0-9.-]+(:[a-zA-Z0-9._-]+)+$`

Publisher guidance by context (see `urn-naming-guide` in the spec for full rationale):
- **Enterprise / own domain** → use the real FQDN everywhere (`urn:air:acme.com:finance:tax`),
  even locally; only the `url` changes between dev and prod.
- **Solo dev, public** → anchor to a namespace you control: `gitlab.com:you:tool`,
  `npmjs.com:you:tool`, `you.github.io:tool`, `you.vercel.app:tool`.
- **Local / private only** → use a reserved placeholder FQDN: `agent.localhost` or
  `example.com`. Never use bare `localhost` as the publisher — it is not globally unique or
  verifiable and breaks federation.

## Media types (the `type` field)
ARD is an envelope; `type` is an IANA media type naming the wrapped artifact. Common values:

| `type` | Resource |
| :-- | :-- |
| `application/mcp-server-card+json` | MCP server (card form, used in the spec/schema) |
| `application/a2a-agent-card+json` | A2A agent card |
| `application/ai-skill` (or `+md`) | A skill |
| `application/ai-catalog+json` | A nested sub-catalog (inline `data` or referenced `url`) |
| `application/ai-registry+json` | A dynamic registry search endpoint |
| `application/parquet`, etc. | Any other artifact (datasets, files) |

The validator only warns when `type` is not a media type (no `/`); it does not hard-code an
allow-list, because the envelope is deliberately open. Per spec §3.3, the de-facto types
`application/a2a-agent-card+json` and `application/mcp-server-card+json` are still tracking
toward formal IANA registration and their exact form may change, so intermediaries are advised
not to strictly verify them — another reason the validator warns rather than rejects.

## Strict Value-or-Reference
An entry MUST carry **exactly one** of:
- `url` — an HTTPS reference to fetch the artifact document, or
- `data` — the full artifact document inline as a JSON object.

Both present, or neither present, is invalid. Use `url` for live/large artifacts; use `data`
to inline a small, self-contained card or a nested `application/ai-catalog+json` bundle.

## Trust manifest
Optional per-entry (and per-host) object carrying verifiable identity and compliance signals.
ARD *communicates* trust evidence; it never confers trust — clients verify independently.

| Field | Required | Notes |
| :-- | :-- | :-- |
| `identity` | yes | Cryptographic principal: SPIFFE ID, `did:web`, or HTTPS URI. Its domain SHOULD align with the URN publisher. |
| `identityType` | no | `spiffe` / `did` / `https` / `other`. |
| `attestations[]` | no | Each requires `type`, `uri`, **`mediaType`**; optional `digest` (sha256). |
| `provenance[]` | no | Each requires `relation` (`derivedFrom`/`publishedFrom`/`copiedFrom`) and `sourceId`; optional `sourceDigest`. |
| `signature` | no | Detached JWS over the trust manifest. |

Note: `mediaType` on each attestation is **required** by the schema and CDDL even though the
prose table in `ard.md §5.2` omits it. Follow the schema.

## Known doc inconsistencies
The bundled docs disagree in a few places. The validator treats the **schema + `ard.md` spec**
as authoritative:
- URN NID: spec/schema use `urn:air:`; some website pages show `urn:ai:`. Use **`urn:air:`**.
- MCP type: spec/schema show `application/mcp-server-card+json`; some pages show
  `application/mcp-server+json`. Both appear in the wild; the validator accepts any media type
  but the templates use the spec form.
