---
name: ard-registry-builder
description: >-
  Build, validate, test, and update registries and catalogs that follow the Agentic Resource
  Discovery (ARD) specification. Use this whenever the user works with an ai-catalog.json,
  a capability manifest, an ARD/AIR catalog or Agent Registry, urn:air: identifiers,
  trustManifest/attestations, representativeQueries, or an Agent Finder / discovery service —
  including authoring a new manifest, scaffolding one, fixing schema or URN errors, running
  conformance/validation, probing a registry's /search, /explore, or /agents REST endpoints,
  reviewing trust and federation metadata, or preparing to publish at /.well-known/ai-catalog.json.
  Trigger it even when the user only says "ARD", "agentic resource discovery", "AI catalog
  manifest", "agent registry", or "make agents discoverable" without naming the file.
license: MIT
metadata:
  author: webmaxru
  version: "1.1"
---

# ARD Registry Builder

Agentic Resource Discovery (ARD) lets AI clients **discover** agents, MCP servers, skills, and
APIs at runtime by search instead of hardcoding them. Publishers describe their resources in a
static `ai-catalog.json` **capability manifest**; dynamic **Agent Registries** index those
manifests and answer `POST /search`. This skill helps you engineer both — author, validate,
test, and maintain them so they actually pass conformance and get discovered.

Two artifacts, one mental model — **identity vs location**:
- The **manifest** (`ai-catalog.json`, static) lists entries. Each entry's `identifier` is a
  permanent `urn:air:` URN (identity); its `url`/`data` is the movable endpoint (location).
- The **registry** (REST API, dynamic) is a service that searches indexed entries.

Never bake a hostname into a URN; never treat a URL as an identity. Almost every ARD mistake
traces back to confusing these two.

## Bundled tools (use these — don't reinvent them)
All scripts are stdlib-only Python 3.8+; `validate_catalog.py` uses the `jsonschema` library
when present (recommended: `pip install jsonschema`) and falls back to a built-in checker.

| Tool | Purpose |
| :-- | :-- |
| `scripts/validate_catalog.py <path-or-url> [--json] [--strict]` | Validate a manifest: JSON Schema **plus** ARD semantic rules. Exit 1 on errors. |
| `scripts/test_registry.py <base-url> [--query T] [--json]` | Probe a live registry's `/search` (required), `/agents`, `/explore` for conformance. |
| `scripts/new_catalog.py --template minimal\|enterprise\|local-dev [--publisher D] [--host N] --out F` | Scaffold a starter manifest. |
| `assets/ai-catalog.schema.json` | The authoritative JSON Schema (Draft 2020-12), bundled for offline validation. |
| `assets/templates/*.json` | Valid starting points: `minimal`, `enterprise` (trust + registry entry), `local-dev`. |

Always **validate after every edit**, and validate the **live URL** after publishing — not just
the local file.

## Decide what the user needs
- *"Create / scaffold / start a catalog"* → **Workflow 1**.
- *"Validate / check / is this valid / why won't it pass conformance / fix this manifest"* →
  **Workflow 2** (run `validate_catalog.py` first, before reading anything).
- *"Test / probe my registry / does my /search work / is my API ARD-compliant"* → **Workflow 3**.
- *"Add an agent / bump a version / change an endpoint / maintain"* → **Workflow 4**.
- *"How does X work" (data model, API, trust, publishing)* → read the matching reference below.

## Workflow 1 — Build a manifest
1. Pick the closest template and scaffold it:
   `python scripts/new_catalog.py --template enterprise --publisher mycorp.com --host "MyCorp AI" --out ./ai-catalog.json`.
   (Without scaffolding, copy a file from `assets/templates/`.)
2. For each resource, set `identifier` (`urn:air:<publisher>:<namespace?>:<name>`),
   `displayName`, `type` (the artifact's media type), and **exactly one** of `url` or `data`.
3. Add `description`, `tags`, `capabilities`, and especially `representativeQueries` (2–5) —
   the single biggest lever for being found by semantic search.
4. Add `trustManifest` only when you have real identity/attestations; keep simple entries lean.
5. Choose the publisher domain to match the deployment context (enterprise FQDN, public
   namespace like `github.com:you`, or `agent.localhost`/`example.com` for local-only). See
   `references/data-model.md`.
6. Validate: `python scripts/validate_catalog.py ./ai-catalog.json`. Fix until it passes.

## Workflow 2 — Validate / debug a manifest
1. **Run the validator first**, before reading the file by hand — it pinpoints issues fast:
   `python scripts/validate_catalog.py <path-or-url>`.
2. Read findings by severity. **ERROR** must be fixed; **WARN** should be (use `--strict` in CI
   to enforce); **INFO** is advice. Every finding names a JSON path and a stable `code`.
3. Map the `code` to a fix using `references/validation-rules.md`. The high-frequency ones:
   - `urn-wrong-nid` → change `urn:ai:` to `urn:air:`.
   - `value-or-reference` → keep exactly one of `url` / `data`.
   - `schema` (oneOf/required/pattern/minItems) → fix the structure the message names.
   - `urn-localhost` / `urn-publisher-fqdn` → use a verifiable or reserved-placeholder domain.
   - `trust-domain-mismatch` → make the `trustManifest.identity` domain match the URN publisher.
4. Re-run until clean. For CI, use `--json` (machine output) and/or `--strict` (fail on warnings).

## Workflow 3 — Test a live registry API
1. Probe it: `python scripts/test_registry.py https://registry.example.com/api/v1`.
   The tester sends a real `POST /search`, validates the `results` envelope (each item is a
   catalog entry carrying a `score` 0–100 and a `source`), confirms a malformed request is
   rejected with `400 + errorCode + message`, and checks optional `/agents` and `/explore`
   (skipped, not failed, when a server returns `404`/`501`).
2. Required checks failing → the server is not ARD-conformant on the mandated floor (`/search`).
   Fix the envelope/status against `references/registry-api.md`.
3. For exploratory calls, hit endpoints directly with `curl` (see `references/registry-api.md`).

## Workflow 4 — Update / maintain
1. Edit the entry. **Keep the `identifier` URN stable** — it is a permanent contract. To move an
   endpoint, change `url` (or `data`), never the URN.
2. Bump the entry's `version` and refresh `updatedAt` (ISO 8601) when the artifact changes.
3. Adding a resource → append an entry; ensure its `identifier` is unique (the validator flags
   duplicates).
4. Re-validate the file; if it is already published, also validate the live URL and re-probe any
   registry. Treat "passes validation" as the definition of done.

## Golden rules (the why behind the checks)
- **URN = identity, url/data = location.** Stable URNs keep search indexes, client references,
  and orchestration working while infrastructure moves underneath them.
- **The publisher segment must be a verifiable FQDN.** Registries extract it and bind it to
  `trustManifest.identity` to stop namespace squatting. `localhost` and bare words break this.
- **Exactly one of `url` or `data`.** Predictable parsing in enterprise pipelines depends on it.
- **`score` is relevance, not trust.** Never gate safety on a search score; verify
  `trustManifest` independently.
- **Validate early, validate often, validate the live URL.** Most "it won't index" problems are
  schema or hosting issues a 1-second validator run would have caught.

## Reference files
Read the one matching the task; each has a table of contents.
- `references/data-model.md` — manifest/entry fields, URN format, media types, value-or-reference,
  trust manifest, and the known `urn:air:` vs `urn:ai:` doc inconsistencies.
- `references/registry-api.md` — `/search`, `/explore`, `/agents`, the query/filter model,
  federation modes, and error codes.
- `references/validation-rules.md` — every check the validator runs, with its `code` and severity.
- `references/publishing.md` — well-known URI, CORS, DNS discovery, and public reference
  registries to test against.

## Evals
`evals/evals.json` holds realistic task prompts for the skill-creator evaluation loop. Use it to
benchmark or regression-test changes to this skill.
