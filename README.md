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

## Run the demo

The exact 30-minute script, commands, expected outputs, timing cutoffs, and recovery checkpoints are
in [`DEMO-RUNBOOK.md`](DEMO-RUNBOOK.md).

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\preflight.ps1
```

The preflight verifies APM 0.28.0, warms the public release, runs the 31-check audit, and resets the
ignored `.demo-live` workspace.
