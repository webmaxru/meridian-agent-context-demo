# Meridian Agent Context Supply Chain

This public conference demo shows how Meridian, a fictional fintech team, turns reviewed AI-agent
skills into pinned, hash-verified dependencies with [Agent Package Manager
(APM)](https://microsoft.github.io/apm/).

The repository contains two deliberately separate trust zones:

- `registry/` is the reviewed source catalog owned by Meridian Platform Engineering.
- `demo/` and `.demo-live/` are the consumer-side walkthrough for `meridian-checkout`.

The live session follows one skill from quarantine to a trusted release, then into an APM manifest,
lockfile, multi-harness deployment, policy check, and required CI gate.

> This repository is intentionally public so the live install needs no token. In a real company,
> the same pattern works with a private Git host and read-only CI credentials.

## Released catalog

The `v1.0.0` tag contains Meridian's first approved skill:

```text
webmaxru/meridian-agent-context-demo/registry/skills/secure-payment-review#v1.0.0
```

## Demo

After the full demo assets land on `main`, use `DEMO-RUNBOOK.md` for the exact, timed walkthrough.

