# Publishing & Discovery Reference

How a finished, validated `ai-catalog.json` becomes discoverable. Publishing makes you
*crawlable*; it does not guarantee any particular discovery service will index you — each one
decides what to include. Inside enterprises, resources are often gathered through an internal
registry or curated inventory instead of open crawling, so confirm your org's pipeline.

## Step 1 — Host the manifest at the well-known path
Serve the validated manifest at:
```
https://<your-domain>/.well-known/ai-catalog.json
```
Requirements for crawlers to fetch it reliably:
- **HTTPS only.**
- `Content-Type: application/json`.
- `Access-Control-Allow-Origin: *` (CORS) — crucial; browser-based crawlers fail without it.

## Step 2 — Advertise it (one or more discovery mechanisms)
Publishers can surface the manifest through any of:
- **Well-Known URI** — the default above; nothing else needed if you can host there.
- **Agentmap directive** in `robots.txt`: `Agentmap: https://example.com/ai-catalog.json`.
- **HTML `<link>`** in a page `<head>`: `<link rel="ai-catalog" href="https://example.com/ai-catalog.json">`.
- **DNS records** when you cannot use the well-known path:

| Name / Host | Type | Value |
| :-- | :-- | :-- |
| `_catalog._agents.<domain>` | `TXT` | `"url=https://bucket.s3.amazonaws.com/ai-catalog.json"` |
| `_search._agents.<domain>` | `SRV` | port `443`, target `search.<domain>` (for a dynamic registry endpoint) |

## Step 3 — Verify what you published
Re-run validation against the **live URL**, not just the local file, to catch hosting issues
(wrong content-type, redirects, partial deploys):
```bash
python scripts/validate_catalog.py https://<your-domain>/.well-known/ai-catalog.json
```
If you also run a dynamic registry, probe it:
```bash
python scripts/test_registry.py https://registry.<your-domain>/api/v1
```

## Local development without publishing
You do not need a domain or cloud identity to build and test. Use the `local-dev` template:
URNs anchored to `agent.localhost`, endpoints pointing at `http://localhost:...`. The manifest
passes conformance while staying entirely local. When you later publish under a real domain,
keep the **URN stable** and only change the `url` (see the data-model "identity vs location"
rule).

## Reference implementations to test against
Public ARD services you can query to sanity-check client behavior or compare envelopes:
- **GitHub Agent Finder** — `POST https://agentfinder.github.com/api/v1/search`.
- **Hugging Face Discover** — REST at `https://huggingface-hf-discover.hf.space/search`;
  also via the `hf discover` CLI.
- **Cisco AI Catalog** — manifest at `https://ai-catalog.outshift.io/.well-known/ai-catalog.json`.

Example smoke test of a live registry's search:
```bash
curl -s https://agentfinder.github.com/api/v1/search \
  -H 'content-type: application/json' \
  -d '{"query":{"text":"summarize a PDF"},"pageSize":3}' \
  | jq '.results[] | {displayName, type, url, score}'
```
