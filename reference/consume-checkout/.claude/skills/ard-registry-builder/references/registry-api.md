# ARD Registry REST API

The authoritative definition is the bundled-by-reference OpenAPI 3.1 spec
(`spec/schemas/ard.openapi.yaml` in the spec repo; summarized here). A compliant
**Agent Registry** is any service that indexes catalog entries and exposes this HTTP
interface. The mandated floor for interoperability is `POST /search`; everything else is
optional.

## Table of contents
- [Endpoints at a glance](#endpoints-at-a-glance)
- [The shared query model](#the-shared-query-model)
- [POST /search (required)](#post-search-required)
- [POST /explore (optional)](#post-explore-optional)
- [GET /agents (optional)](#get-agents-optional)
- [Filter semantics](#filter-semantics)
- [Federation](#federation)
- [Errors](#errors)
- [Discovering a registry's base URL](#discovering-a-registrys-base-url)

## Endpoints at a glance
| Method + path | Required? | Purpose | Absence signal |
| :-- | :-- | :-- | :-- |
| `POST /search` | **Required** | Semantic, ranked search | — |
| `POST /explore` | Optional | Facet aggregation over the matched set | `501 Not Implemented` |
| `GET /agents` | Optional | Deterministic, cacheable listing | `404`/`501` |

A registry MAY additionally expose search as an MCP tool or A2A skill, but the REST floor
must exist regardless.

## The shared query model
`search` and `explore` share a `query` object:
```json
{ "query": { "text": "find me a flight booking agent",
             "filter": { "type": ["application/a2a-agent-card+json"], "tags": ["finance"] } } }
```
- `text` — natural-language need; narrows by semantic relevance.
- `filter` — structured constraints (see [Filter semantics](#filter-semantics)).
- For **search**, `text` is required and `filter` optional. For **explore**, both are optional.

## POST /search (required)
Request adds root-level `federation` (`auto` default / `referrals` / `none`), `pageSize`
(default 10, max 100), `pageToken`.

Response envelope:
```json
{
  "results": [
    { "identifier": "urn:air:acme.com:agent:assistant", "displayName": "...",
      "type": "application/a2a-agent-card+json", "url": "https://...",
      "score": 95, "source": "https://registry.acme.com/api/v1/" }
  ],
  "referrals": [ { "identifier": "...", "displayName": "...",
                   "type": "application/ai-registry+json", "url": "https://..." } ],
  "pageToken": "..."
}
```
Each result is a **catalog entry** (same shape as in a manifest) plus two required fields:
- `score` — integer 0–100, semantic relevance only. Clients **MUST NOT** read it as trust,
  compliance, or safety. Verify trust separately via `trustManifest`.
- `source` — base URL of the registry that indexed the entry.

`referrals` appears only in `referrals` federation mode.

## POST /explore (optional)
Returns aggregated facets rather than ranked entries — useful to introspect a registry
("which media types / publishers exist?").
```json
{ "query": { "text": "currency conversion" },
  "resultType": { "facets": [ { "field": "type" }, { "field": "publisher", "limit": 50 } ] } }
```
Response: `{ "resultType": "facets", "facets": { "type": { "buckets": [ { "value": "...", "count": 1247 } ], "otherCount": 23 } } }`.
Facets are computed over the **whole** matched set, not one page. A registry that does not
implement explore returns `501`.

## GET /agents (optional)
Deterministic browsing for developer portals. Query params: `filter` (EBNF expression,
e.g. `type = 'application/mcp-server-card+json' AND createdAfter > '2026-01-01'`), `orderBy`
(e.g. `updatedAt DESC`), `pageSize` (default 20, max 100), `pageToken`. Response:
`{ "items": [ <catalog entry>, ... ], "total": 42, "pageToken": "..." }`. No relevance sorting.

EBNF filter fields (Appendix A): `displayName`, `type` (comma = OR), `publisherId` (comma = OR),
`createdAfter`, `updatedAfter`. AND across fields; OR within a field.

## Filter semantics
For the `query.filter` object (search/explore):
- Keys are **dot-separated field paths** into a catalog entry, e.g. `type`, `tags`,
  `capabilities`, `trustManifest.attestations.type`, `metadata.region`.
- `publisher` is a **derived** key — the registry extracts it from the URN, it is not stored.
- Values are arrays (a bare scalar counts as a one-element array).
- **Within a key → OR**; **across keys → AND**. When a path resolves to an array on the entry,
  a constraint matches if any element satisfies it.
- Any present attribute MAY be a filter key (including `metadata.*` and Schema.org fields). A
  registry MAY reject an unsupported field path with `400`.

## Federation
The client controls topology via `federation`:
- `auto` — registry queries upstreams, merges, returns one unified result set.
- `referrals` — registry returns its own results plus `referrals` (other registries) for the
  client to follow itself.
- `none` — local index only.

Explore does **not** federate; it is always scoped to the queried registry.

## Errors
Uniform body: `{ "errorCode": "INVALID_ARGUMENT", "message": "..." }`.

| HTTP | `errorCode` | When |
| :-- | :-- | :-- |
| 400 | `INVALID_ARGUMENT` | Malformed query / invalid filter syntax (e.g. missing `query.text`). |
| 401 | `UNAUTHENTICATED` | Missing/invalid credentials. |
| 404 | `NOT_FOUND` | Unknown agent or registry. |
| 429 | `RATE_LIMIT_EXCEEDED` | Too many requests. |
| 500 | `INTERNAL_ERROR` | Server failure. |
| 501 | — | `POST /explore` not implemented. |

`scripts/test_registry.py` verifies the required `/search` behavior (including the 400 on a
missing `query.text`) and treats `/agents` and `/explore` as optional (skipped when absent).
It mirrors the registry mode of the spec's official conformance CLI
(`conformance/bin/conformance-test registry <base-url>`), the canonical reference you can run
as a cross-check.

## Discovering a registry's base URL
Inside a static manifest, a dynamic registry advertises itself as an entry of type
`application/ai-registry+json` whose `url` is the API base. Clients read that `url` and then
call `POST {base}/search`. DNS `SRV` records under `_search._agents.<domain>` are an
alternative discovery path.
