# Build a Supply Chain for Agent Context

**30-minute, demo-first conference runbook**
**Verified:** 2026-08-25 with Agent Package Manager CLI **0.28.0**

This talk uses **Meridian**, the fictional fintech from *The Missing Package Manager*. Meridian's
six-person `meridian-checkout` team uses GitHub Copilot, Claude Code, and Cursor. The narrow story
for this session is:

> The team wants useful agent skills, but copying an arbitrary `SKILL.md` from the internet gives
> them no review, provenance, reproducibility, or policy. They create a reviewed catalog, pin one
> approved skill in the service manifest, let APM resolve and hash it for every harness, and make the
> same audit a required pull-request check.

APM means **Agent Package Manager** in this talk, not application performance monitoring.

## What the audience sees

| Time | Surface | Outcome |
| ---: | --- | --- |
| 00:00-01:20 | Slide 1 | Hook: a text file is still a supply-chain input |
| 01:20-04:30 | VS Code + terminal | Reject a downloaded skill; pass the reviewed one |
| 04:30-05:30 | Slide 2 | Visualize quarantine -> review -> release -> install -> gate |
| 05:30-10:30 | VS Code + terminal | Install one pinned skill for Copilot, Claude, and Cursor |
| 10:30-14:30 | VS Code + terminal | Read tag, commit, package hash, and deployed-file hashes |
| 14:30-18:30 | VS Code + terminal | Add the trusted-source policy and run the clean audit |
| 18:30-19:30 | Slide 3 | Visualize why the CI control is authoritative |
| 19:30-24:30 | VS Code + GitHub | Show the pinned workflow, CODEOWNERS, and required check |
| 24:30-25:30 | Slide 4 | Close on owner + version + hash + gate |
| 25:30-30:00 | Slide 4 | Questions and recovery buffer |

The schedule intentionally budgets about ten times more explanation time than command time.

## Before the session

### 1. Prepare the repository

```powershell
Set-Location "$HOME\Downloads\projects\meridian-agent-context-demo"
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\preflight.ps1
```

Expected final lines:

```text
Preflight PASS
APM: Agent Package Manager (APM) CLI version 0.28.0
Release: v1.0.0 is reachable
Reference: install + 31-check audit passed
Workspace: .demo-live reset to the opening state
```

Measured preflight time: **14-33 seconds** across rehearsals. Run it before the session; it warms
the package cache, proves the reference state, and recreates `.demo-live` without changing tracked
files.

### 2. Prepare the screens

Open the repository root in VS Code. Set terminal font to at least 18 px and keep the terminal at
the repository root. Pre-open these files in this order:

1. `.demo-live/meridian-checkout/src/refund.ts`
2. `.demo-live/quarantine/refund-helper/SKILL.md`
3. `registry/skills/secure-payment-review/SKILL.md`
4. `.demo-live/meridian-checkout/apm.yml`
5. `demo/snippets/apm-policy.yml`
6. `.github/workflows/apm-supply-chain.yml`
7. `.github/CODEOWNERS`

Open the local slide deck separately:

```powershell
Start-Process .\slides\index.html
```

Press `F` once the deck opens. Fullscreen hides the small presenter-control strip from the
projector; `N` still toggles speaker notes during rehearsal.

For the deck in the book repository, use:

```powershell
Start-Process "$HOME\Downloads\projects\agent-package-manager-book\slides\index.html"
```

Open these browser tabs behind the deck:

- <https://github.com/webmaxru/meridian-agent-context-demo/releases/tag/v1.0.0>
- <https://github.com/webmaxru/meridian-agent-context-demo/actions/workflows/apm-supply-chain.yml>
- <https://github.com/webmaxru/meridian-agent-context-demo/settings/branches>

Do not open a live Copilot chat during the critical path. Agent response latency is nondeterministic,
and the session is about supplying the context, not evaluating one model response.

## Live script

### 00:00-01:20 - Slide 1: the uncomfortable equivalence

**Show:** Slide 1, `Build a Supply Chain for Agent Context`.

**Say:**

> You would never pipe a random internet script into your build. Yet teams copy `SKILL.md` files
> from the internet into an agent that can edit code, call tools, and influence a pull request. That
> is a supply-chain decision disguised as a text file.

> Meridian already signs, pins, and scans application dependencies. In the next 24 minutes, we give
> its agent context an owner, a version, a hash, and a gate.

Point out once: **APM here is Agent Package Manager.**

**Switch:** VS Code, `src/refund.ts`.

### 01:20-04:30 - Demo 1: quarantine before trust

#### Show the pressure

**Show:** `.demo-live/meridian-checkout/src/refund.ts`.

Call out the obvious payment-review needs: floating-point money, card data in logs, and a retry
without an idempotency key. The team naturally wants a reusable review skill.

**Show:** `.demo-live/quarantine/refund-helper/SKILL.md`.

**Say:**

> Anika found this helper online. It looks like ordinary Markdown. Nobody at Meridian owns it, and
> the editor cannot show us everything that is in it.

From the repository root, run:

```powershell
apm audit --file .\.demo-live\quarantine\refund-helper\SKILL.md --verbose
```

Expected in about **2.5 seconds**, exit `1`:

```text
CRITICAL ... U+202E ... Right-to-left override (RLO)
[x] 1 critical finding(s) ... hidden characters detected
```

**Say:**

> A readable file can carry unreadable instructions. This scanner does not claim to understand
> intent or detect every prompt injection. It gives us a concrete first gate: hidden Unicode does
> not enter the catalog.

**Show:** `registry/skills/secure-payment-review/SKILL.md`, then run:

```powershell
apm audit --file .\registry\skills\secure-payment-review\SKILL.md --verbose
```

Expected in about **2 seconds**, exit `0`:

```text
[*] 1 file(s) scanned -- no issues found
```

Show the metadata owner and the narrow required checks. Briefly point to `.github/CODEOWNERS`.

**Say:**

> We did not ban reuse. We moved trust earlier: review once, assign an owner, and release the result.

### 04:30-05:30 - Slide 2: the route

**Show:** Slide 2.

Read the route left to right:

```text
quarantine -> review -> v1.0.0 -> apm.yml -> apm.lock.yaml -> native harness paths
```

**Say:**

> The release is the trusted source. The manifest is intent. The lockfile is evidence. Policy
> decides whether this source is allowed at all.

**Switch:** VS Code, `.demo-live/meridian-checkout/apm.yml`.

### 05:30-10:30 - Demo 2: install the approved dependency

**Show:** `.demo-live/meridian-checkout/apm.yml`.

Point at exactly three things:

1. `targets`: Claude, Copilot, Cursor.
2. `dependencies.apm`: the reviewed repository path.
3. `#v1.0.0`: the release constraint; no branch tip and no copy-paste.

**Say:**

> This line replaces the wiki checklist. It says which reviewed context this repository depends on,
> and the repository commits it like any other dependency declaration.

Run:

```powershell
Set-Location .\.demo-live\meridian-checkout
apm install
```

Measured warm run: **13.5 seconds**. Budget **20 seconds** before using the fallback. The command may
print a non-fatal warning that `webmaxru/.github-private` was not found; that is APM looking for an
organization policy in a personal-account demo. The explicit local policy arrives in the next beat.

Expected key lines:

```text
Targets: claude, copilot, cursor  (source: apm.yml)
...secure-payment-review#v1.0.0 ... @40a6cabc
|-- Skill integrated -> .agents/skills/, .claude/skills/
```

Show what landed:

```powershell
Get-ChildItem -File -Recurse .agents,.claude | Resolve-Path -Relative
apm deps list
```

Expected files:

```text
.\.agents\skills\secure-payment-review\SKILL.md
.\.claude\skills\secure-payment-review\SKILL.md
```

Explain the current **0.28.0** path model precisely:

- Copilot and Cursor share the converged `.agents/skills` path.
- Claude Code receives its native `.claude/skills` path.
- One source skill is deployed without keeping three hand-edited copies.

### 10:30-14:30 - Demo 3: make reproducibility visible

**Open:** `.demo-live/meridian-checkout/apm.lock.yaml`.

Or print the compact proof:

```powershell
Get-Content .\apm.lock.yaml -TotalCount 24
```

Point at:

1. `resolved_ref: v1.0.0` - the human release.
2. `resolved_commit: 40a6c...` - the immutable source revision.
3. `content_hash` - the resolved package content.
4. `deployed_file_hashes` - what actually reached each harness path.

**Say:**

> The tag is human meaning. The commit is immutable source. The hashes are evidence. If a deployed
> skill changes behind APM's back, the CI audit detects hash drift.

Do not improvise a live `--frozen` mismatch. On APM 0.28.0, changing between two refs that resolve to
the same commit can cause `apm install --frozen` to rewrite the lockfile and still exit `0`. The
authoritative demo control is the full `apm audit --ci` gate shown next.

### 14:30-18:30 - Demo 4: add the sourcing policy

Copy the prepared policy into the consumer:

```powershell
Copy-Item ..\..\demo\snippets\apm-policy.yml .\apm-policy.yml
```

**Open:** `.demo-live/meridian-checkout/apm-policy.yml`.

Point at:

- `enforcement: block`
- `fetch_failure: block`
- the allowlist for `webmaxru/meridian-agent-context-demo` and nested paths
- `require_pinned_constraint: true`

**Say:**

> A lock tells us what we installed. Policy decides whether we were allowed to install it. The
> second `/**` allow pattern matters because the approved skill lives below a repository path.

Validate policy discovery:

```powershell
apm policy status --policy-source .\apm-policy.yml --check
```

Expected in about **1.5 seconds**, exit `0`: policy found, `block`, two allow patterns, no warnings.

Run the same gate CI will run:

```powershell
apm audit --ci --policy .\apm-policy.yml --no-fail-fast
```

Expected in **2-4 seconds**, exit `0`:

```text
[+] No drift detected
[*] All 31 check(s) passed
```

**Say:**

> This rechecks source policy, manifest-to-lock consistency, hashes, hidden Unicode, and deployed
> drift. We are not performing a fake failure for theatre. The setup is the proof; the required
> status check is what makes it authoritative.

### 18:30-19:30 - Slide 3: local checks versus an authoritative gate

**Show:** Slide 3.

**Say:**

> A developer can skip a local command. They cannot merge around a required check unless they also
> have authority to change the separately protected workflow or policy. That repository boundary is
> the trust boundary.

Call out the four protected links:

```text
immutable action -> pinned CLI -> blocking policy -> required status
```

**Switch:** VS Code, `.github/workflows/apm-supply-chain.yml`.

### 19:30-24:30 - Demo 5: show the unbypassable setup

**Show:** `.github/workflows/apm-supply-chain.yml`.

Point at:

1. Minimal `contents: read` permission.
2. `microsoft/apm-action` pinned to immutable commit
   `d723bb64ed70c135bbaf87d126b721dd2dae0439` (release `v1.10.0`).
3. `apm-version: "0.28.0"` because the action's current default is older.
4. `setup-only: true` so the action does not overwrite a tampered deployed file before audit.
5. Policy existence check with `--check --no-cache`.
6. Full audit with `--no-cache --no-fail-fast`.

**Show:** `.github/CODEOWNERS`.

Explain that the catalog, policy, and workflow require platform review. Then switch to the GitHub
Actions tab and show the green `audit` job. Finally show branch protection/rules and the required
`audit` status.

Phrase the guarantee accurately:

> It is unbypassable for an ordinary contributor: no direct push, no merge without `audit`, and no
> workflow or catalog change without the owning review. As with every CI control, organization
> administrators remain the ultimate trust boundary.

### 24:30-25:30 - Slide 4: close

**Show:** Slide 4.

**Say:**

> The skill is no longer an arbitrary file copied from the internet. It is a reviewed source, a
> declared dependency, an immutable resolution, a hashed deployment, and a required policy check.

> Agent context becomes a real dependency when it has four things: an owner, a version, a hash, and
> a gate.

Leave the repository URL on screen:

<https://github.com/webmaxru/meridian-agent-context-demo>

## Recovery plan

Use a hard cutoff. The audience should see the next proof, not watch you debug the previous command.

| Live step | Cutoff | Recovery command | What to say |
| --- | ---: | --- | --- |
| Untrusted file scan | 5 s | `Get-Content .\demo\fallback\01-untrusted-scan.txt` | "Here is the captured 0.28.0 result: critical U+202E, exit 1." |
| Trusted file scan | 7 s | Open the reviewed `SKILL.md`; continue | "The catalog copy passed preflight; the interesting proof is the released install." |
| `apm install` | 20 s | See the checkpoint sequence below | "The network is not the demo. The resolved state is." |
| Lockfile display wraps | immediate | `Get-Content ..\..\demo\fallback\03-lockfile.txt` | "Tag, commit, package hash, deployed-file hashes." |
| Policy status/audit | 10 s | `Get-Content ..\..\demo\fallback\04-audit-pass.txt` | "The preflight ran this exact 31-check gate." |
| GitHub Actions page | 5 s | Stay in the workflow file | "The local command already passed; this file makes it required in CI." |
| Slides fail | immediate | Continue from VS Code | The story and proof are entirely in the repository. |

### Install checkpoint

If `apm install` exceeds 20 seconds, press `Ctrl+C`, then run from
`.demo-live\meridian-checkout`:

```powershell
Set-Location ..\..
.\scripts\jump-to-checkpoint.ps1 -Name installed
Set-Location .\.demo-live\meridian-checkout
Get-Content ..\..\demo\fallback\02-install.txt
```

The checkpoint restores the real generated lockfile and deployed skill files in under one second.

### Governed checkpoint

If the local policy copy or audit state becomes confusing:

```powershell
Set-Location ..\..
.\scripts\jump-to-checkpoint.ps1 -Name governed
Set-Location .\.demo-live\meridian-checkout
Get-Content ..\..\demo\fallback\04-audit-pass.txt
```

### Reset between rehearsals

From the repository root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\reset-demo.ps1
```

Reset time in the dry run: **1.1 seconds**.

## Battle-tested timings

Measured on the presentation machine on 2026-08-25:

| Operation | Result | Wall time |
| --- | --- | ---: |
| Full preflight | PASS | 14.4-32.6 s |
| Reset live workspace | PASS | 1.1-2.2 s |
| Scan hidden U+202E | expected FAIL, exit 1 | 2.5 s |
| Scan reviewed skill | PASS | 1.9 s |
| Install pinned public skill | PASS | 13.5 s warm; 23.9 s cold/network-bound |
| Policy status | PASS | 1.5 s |
| Full 31-check policy audit | PASS | 1.7-3.9 s |
| Restore installed checkpoint | PASS | 0.7 s |

The complete critical path was rehearsed end to end in **72.4 seconds of command time**. Network is
required only to resolve the public GitHub release; every stage after the checkpoint has a local,
committed fallback.
