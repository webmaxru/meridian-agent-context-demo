# Meridian Agent Context Supply Chain

This public consumer/demo repository shows how Meridian, a fictional fintech team, consumes public
agent context and governs company-owned context with [Agent Package Manager
(APM)](https://microsoft.github.io/apm/). The company catalog lives separately in the private
`webmaxru/meridian-agent-context-registry` repository.

The 30-minute story has two parts:

1. **Consuming APM** - install one public skill, declare a shared set of skills and a prompt in
   `apm.yml`, then make the resolved commits and hashes visible in `apm.lock.yaml`.
2. **Governing APM** - install a reviewed skill from Meridian's private registry, allow only that
   source in policy, and require the same audit before a pull request can merge.

The demo uses deliberately separate trust zones:

- `webmaxru/meridian-agent-context-registry` is the reviewed, private source catalog.
- `demo/` contains clean starts, copy-ready snippets, captured output, and recovery material.
- `reference/` contains the verified end states used by preflight, CI, and stage checkpoints.
- `.demo-live/` is the ignored workspace recreated for each rehearsal.

## Private catalog release

The `v1.0.0` tag contains Meridian's first approved skill:

```text
webmaxru/meridian-agent-context-registry/skills/secure-payment-review#v1.0.0
```

## Run the demo

The exact commands, timing cutoffs, and recovery checkpoints are in
[`DEMO-RUNBOOK.md`](DEMO-RUNBOOK.md). The near-verbatim narration is in
[`TALK-TRACK.md`](TALK-TRACK.md).

```powershell
& .\scripts\preflight.ps1
```

The preflight obtains a session-only GitHub credential without printing it, verifies APM 0.28.0,
warms both reference states, runs the consume and governed audits, and resets `.demo-live`. Hosted
CI reads the same private source through the encrypted `MERIDIAN_REGISTRY_PAT` secret in the
review-protected `meridian-registry` environment.

This conference setup intentionally audits pull requests from trusted branches in this repository.
GitHub does not expose private-registry secrets to fork workflows, so fork pull requests remain
blocked until a maintainer recreates the reviewed change on a repository branch.
