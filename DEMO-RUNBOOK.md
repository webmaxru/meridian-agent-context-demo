# Build a Supply Chain for Agent Context

**30-minute, demo-first conference runbook**
**Verified:** 2026-08-25 with Agent Package Manager CLI **0.28.0**

## Session description

> Your software supply chain is signed, pinned, and scanned in continuous integration. Your AI
> agents' context isn't. Spend a worthwhile 30 minutes with Maxim Salnikov as he builds a supply
> chain for agent context with Agent Package Manager: sourcing approved packages from a trusted
> registry, pinning and hash-verifying them on any harness, and enforcing organization policy with
> an unbypassable CI gate.

In this talk, **unbypassable** is scoped to ordinary contributors. Repository administrators remain
the ultimate trust boundary.

The running project is `meridian-checkout`, owned by Meridian, the fictional fintech from the book.
Lena uses GitHub Copilot, Omar uses Claude Code, and Priya uses Cursor. They want useful agent
skills, but they do not want trust, versioning, or installation to depend on copied files and wiki
instructions.

The live story has two parts:

1. **Consuming APM** - install one public skill, declare a team context set in `apm.yml`, and prove
   its exact resolution and native harness deployment.
2. **Governing APM** - install a reviewed skill from Meridian's private registry, add a blocking
   sourcing policy, and show the required pull-request gate.

The setup uses two repositories because GitHub Free cannot protect branches in private
repositories:

| Trust zone | Repository | Visibility | Purpose |
| --- | --- | --- | --- |
| Consumer and gate | `webmaxru/meridian-agent-context-demo` | Public | Demo project, policy, CI, required `audit` status |
| Company registry | `webmaxru/meridian-agent-context-registry` | Private | Reviewed Meridian skills and release `v1.0.0` |

This separation is intentional: the source can be private while the consumer repository provides a
real, inspectable branch-protection proof.

## Thirty-minute map

| Time | Surface | Outcome |
| ---: | --- | --- |
| 00:00-01:20 | Slide 1 | Agent context is a supply-chain input |
| 01:20-02:35 | Slide 2 | What APM manages and which controls it adds |
| 02:35-03:15 | Slide 3 | Preview the consuming path |
| 03:15-05:45 | VS Code + terminal | Install one released public skill |
| 05:45-08:30 | VS Code + terminal | Install a multi-asset `apm.yml` |
| 08:30-11:30 | VS Code + terminal | Show native paths, lock evidence, frozen replay, and audit |
| 11:30-12:15 | Slide 4 | Preview the governing path |
| 12:15-15:45 | VS Code + terminal | Install Meridian's private reviewed skill |
| 15:45-19:30 | VS Code + terminal | Add blocking sourcing policy and run the 31-check audit |
| 19:30-24:30 | VS Code + GitHub | Show pinned workflow, secret, CODEOWNERS, and required status |
| 24:30-25:00 | Slide 5 | Close on owner, version, hash, and gate |
| 25:00-30:00 | Slide 5 | Questions and recovery buffer |

The critical-path APM commands took **79.740 seconds** in the full dry run. The remaining time is
for explanation, file inspection, transitions, and audience questions.

## Before the session

### 1. Keep both repositories side by side

Expected local paths:

```text
$HOME\Downloads\projects\meridian-agent-context-demo
$HOME\Downloads\projects\meridian-agent-context-registry
```

Open the demo repository in VS Code. Open the private registry in a second window, or add it as a
second workspace folder. Set the terminal font to at least 18 px.

### 2. Run preflight in the terminal you will keep open

```powershell
Set-Location "$HOME\Downloads\projects\meridian-agent-context-demo"
& .\scripts\preflight.ps1
```

Run the script with `&`, not through a separate `powershell -File` process. Preflight obtains the
current `gh` credential and leaves `GITHUB_APM_PAT` in this terminal process without printing it.
Keep this terminal open for the demo.

Expected final lines:

```text
Preflight PASS
APM: Agent Package Manager (APM) CLI version 0.28.0
Public source: ai-native-dev v1.9.0 is reachable
Private source: meridian-agent-context-registry v1.0.0 authenticated (credential not printed)
Consume reference: frozen replay + audit passed
Govern reference: frozen replay + policy audit passed
Workspace: .demo-live reset to both opening states
```

Measured preflight time: **44.97 seconds**. It verifies both sources, warms the machine cache, tests
the frozen and governed references, removes reference-local package caches, and resets `.demo-live`.

### 3. Pre-open the files

In the demo repository:

1. `.demo-live/consume-checkout/src/refund.ts`
2. `demo/snippets/apm-consume.yml`
3. `.demo-live/governed-checkout/apm.yml`
4. `demo/snippets/apm-policy.yml`
5. `.github/workflows/apm-supply-chain.yml`
6. `.github/CODEOWNERS`

In the private registry:

1. `skills/secure-payment-review/SKILL.md`
2. `.github/CODEOWNERS`

Open these authenticated browser tabs:

- <https://github.com/webmaxru/meridian-agent-context-registry>
- <https://github.com/webmaxru/meridian-agent-context-demo/actions/workflows/apm-supply-chain.yml>
- <https://github.com/webmaxru/meridian-agent-context-demo/settings/branches>

Open the deck:

```powershell
Start-Process .\slides\index.html
```

Press `F` for fullscreen. `N` toggles concise speaker notes during rehearsal.

## Live demo: Part 1 - Consuming APM

### 03:15-05:45 - Install one public skill

Start at the repository root:

```powershell
Set-Location .\.demo-live\consume-checkout
apm init --yes --target copilot
apm install 'webmaxru/ai-native-dev/skills/agent-package-manager#v1.9.0'
```

The single quotes are deliberate: they keep the `#v1.9.0` pin intact in PowerShell and other
shells that treat `#` as a comment marker.

Expected proof:

```text
[+] webmaxru/ai-native-dev/skills/agent-package-manager#v1.9.0
[*] Updated apm.yml with 1 new package
#v1.9.0 @d04f0b01
|-- Skill integrated -> .agents/skills/
[*] Installed 1 APM dependency
```

Measured wall times:

- `apm init`: **1.747 seconds**
- direct install: **20.553 seconds**

Open the generated `apm.yml`. Point out that the command added a declared, release-pinned
dependency rather than leaving an unexplained copied folder.

**Hard cutoff:** 30 seconds for the install. If it is still resolving, use the `consume-single`
checkpoint.

### 05:45-08:30 - Move from individual use to a team manifest

Show `demo/snippets/apm-consume.yml`. It contains only external assets from
`webmaxru/ai-native-dev`:

- three human-readable `v1.9.0` release pins;
- two full immutable commit pins;
- four skills;
- one prompt;
- explicit Claude, Copilot, and Cursor targets.

Copy the prepared manifest and install it:

```powershell
Copy-Item ..\..\demo\snippets\apm-consume.yml .\apm.yml
apm install
```

Expected proof:

```text
Targets: claude, copilot, cursor
4 skills -> .agents/skills/, .claude/skills/
1 prompt -> .github/prompts/
2 command adapters -> .claude/commands/, .cursor/commands/
[*] Installed 5 APM dependencies
```

Measured wall time: **13.235 seconds** warm. A mostly cold rehearsal took about 35 seconds.

The prompt adapter may report that unsupported `agent` and `name` frontmatter keys were dropped for
Claude and Cursor. That is expected target adaptation, not an installation failure. Do not execute
the installed version/deploy prompt during the session.

**Hard cutoff:** 60 seconds. Recover with `consume-manifest`.

### 08:30-11:30 - Make reproducibility visible

Show the native deployment paths:

```powershell
Get-ChildItem -File -Recurse .agents\skills,.claude\skills -Filter SKILL.md |
  Resolve-Path -Relative
Get-Item .github\prompts\*.prompt.md,.claude\commands\*.md,.cursor\commands\*.md |
  Resolve-Path -Relative
```

Open `apm.lock.yaml`. Point at one release-pinned skill, one full-SHA-pinned skill, and the prompt.
For each, identify:

1. `resolved_ref`
2. `resolved_commit`
3. `content_hash`
4. `deployed_file_hashes`, which are APM's normalized deployed-content hashes

Then prove a frozen replay leaves the lockfile byte-identical:

```powershell
$before = (Get-FileHash .\apm.lock.yaml -Algorithm SHA256).Hash
apm install --frozen
$after = (Get-FileHash .\apm.lock.yaml -Algorithm SHA256).Hash
$before
$after
"LOCK_UNCHANGED=$($before -eq $after)"
```

Historical dry-run capture:

```text
575A76EEAFF620EAF3F9A2E031C85D24DCA265C04B06F99FD79C607A2AAFCFC4
575A76EEAFF620EAF3F9A2E031C85D24DCA265C04B06F99FD79C607A2AAFCFC4
LOCK_UNCHANGED=True
```

The lockfile includes generated metadata, so a fresh mutable install can produce a different
SHA-256. The live proof is that the two values displayed in the same frozen replay are equal.

Finish the consuming half with:

```powershell
apm audit --ci --no-policy
```

Expected:

```text
[+] No drift detected
[*] All 10 check(s) passed
```

Measured times:

- frozen replay: **11.066 seconds**
- consume audit: **5.002 seconds**

APM 0.28.0 can print `Installed 1 APM dependency` at the end of a five-package frozen replay. The
detailed output correctly reports `Replayed 5 package(s)`, and the unchanged lock plus 10-check
audit are the authoritative proof.

## Live demo: Part 2 - Governing APM

### 12:15-15:45 - Install from Meridian's private registry

Show the authenticated GitHub page or the local private-registry file:

```text
meridian-agent-context-registry/skills/secure-payment-review/SKILL.md
```

Call out the narrow behavior, Platform Engineering author, version, and owner. Then move to the
governed workspace:

```powershell
Set-Location ..\..
Set-Location .\.demo-live\governed-checkout
apm install 'webmaxru/meridian-agent-context-registry/skills/secure-payment-review#v1.0.0'
```

The session credential was loaded by preflight and is not printed. Expected proof:

```text
[+] webmaxru/meridian-agent-context-registry/skills/secure-payment-review#v1.0.0
#v1.0.0 @5b105da7
|-- Skill integrated -> .agents/skills/, .claude/skills/
[*] Installed 1 APM dependency
```

Lock evidence:

```text
resolved_commit: 5b105da760849b41b94a16ca043754e5336f84b6
content_hash: sha256:54bda74d0776581d8ca64b4849cf6f096070801dbf2e7557f663eac544274016
deployed_file_hashes: 2
```

Measured wall time: **24.666 seconds**. APM may report that a partial clone fell back to a full bare
clone; that is an automatic transport fallback and the command still verifies the release.

**Hard cutoff:** 40 seconds. Recover with `govern-private`.

### 15:45-19:30 - Add the sourcing policy

Copy the prepared policy:

```powershell
Copy-Item ..\..\demo\snippets\apm-policy.yml .\apm-policy.yml
```

Open `apm-policy.yml` and point at:

- `enforcement: block`
- `fetch_failure: block`
- the private registry allow patterns
- `require_pinned_constraint: true`

The `/**` pattern is required because the approved skill is below a repository path.

Validate discovery, then run the same audit used in CI:

```powershell
apm policy status --policy-source .\apm-policy.yml --check
apm audit --ci --policy .\apm-policy.yml --no-fail-fast
```

Expected:

```text
Outcome: found
Enforcement: block
Effective rules: 2 dependency allow patterns
Warnings: none

[+] No drift detected
[+] All dependencies match allow list
[+] All dependencies use pinned constraints
[*] All 31 check(s) passed
```

Measured times:

- policy status: **1.709 seconds**
- governed audit: **1.762 seconds**

The talk demonstrates the blocking setup, not a staged failure. The successful 31-check audit is the
state the team permits to merge.

### 19:30-24:30 - Show the required CI boundary

Open `.github/workflows/apm-supply-chain.yml` and point at:

1. minimal `contents: read` permission;
2. the review-protected `meridian-registry` environment;
3. its encrypted `MERIDIAN_REGISTRY_PAT` secret mapped to `GITHUB_APM_PAT` only on the audit step;
4. `actions/checkout` pinned to an immutable commit;
5. `microsoft/apm-action` pinned to an immutable commit;
6. explicit APM CLI `0.28.0`;
7. `setup-only: true`, so the action does not repair drift before audit;
8. policy presence check with `--check --no-cache`;
9. full audit with `--no-cache --no-fail-fast`.

Open `.github/CODEOWNERS`, then show the successful hosted `audit` job and `main` protection in
GitHub:

```text
strict required status: audit
administrator enforcement: enabled
approving reviews: 1
CODEOWNERS review: required
private-registry environment approval: required
force pushes: disabled
branch deletion: disabled
linear history: required
conversation resolution: required
```

Use the accurate guarantee:

> This is unbypassable for an ordinary contributor: no direct push and no merge without the
> required audit and owning review. Repository administrators remain the ultimate trust boundary.

The demo's contribution model uses same-repository branches. GitHub does not expose the private
registry environment secret to fork workflows, so a fork pull request cannot satisfy `audit`; a
maintainer must recreate the reviewed change on a trusted repository branch.

## Recovery plan

Use a hard cutoff. The audience should see the next proof, not watch network troubleshooting.

| Live step | Cutoff | Recovery checkpoint or file |
| --- | ---: | --- |
| Direct public install | 30 s | `consume-single` + `demo/fallback/01-consume-single.txt` |
| Five-asset manifest install | 60 s | `consume-manifest` + `demo/fallback/02-consume-manifest.txt` |
| Frozen replay or lock display | 20 s | `consume-manifest` + `demo/fallback/03-reproducibility.txt` |
| Private registry install | 40 s | `govern-private` + `demo/fallback/04-private-registry.txt` |
| Policy status or audit | 10 s | `govern-policy` + `demo/fallback/05-policy-audit.txt` |
| GitHub pages | 5 s | Keep workflow open + `demo/fallback/06-required-gate.txt` |
| Slides | immediate | Continue from VS Code; every proof is in the repositories |

From the repository root:

```powershell
Set-Location "$HOME\Downloads\projects\meridian-agent-context-demo"
.\scripts\jump-to-checkpoint.ps1 -Name consume-single
.\scripts\jump-to-checkpoint.ps1 -Name consume-manifest
.\scripts\jump-to-checkpoint.ps1 -Name govern-private
.\scripts\jump-to-checkpoint.ps1 -Name govern-policy
```

Always run the `Set-Location` line first, because a failed live command leaves the terminal inside a
`.demo-live` workspace. Use only the checkpoint needed for the current beat, then return to that
workspace. Measured restore times:

| Checkpoint | Time |
| --- | ---: |
| `consume-single` | 0.217 s |
| `consume-manifest` | 0.319 s |
| `govern-private` | 0.107 s |
| `govern-policy` | 0.123 s |

Reset between rehearsals:

```powershell
& .\scripts\reset-demo.ps1
```

## Battle-tested timings

Measured on the presentation machine on 2026-08-25:

| Operation | Result | Wall time |
| --- | --- | ---: |
| Full preflight | PASS | 44.97 s |
| `apm init --yes --target copilot` | PASS | 1.747 s |
| Direct public skill install | PASS | 20.553 s |
| Five-asset manifest install | PASS | 13.235 s |
| Frozen replay | PASS, lock byte-identical | 11.066 s |
| Consume audit | PASS, 10 checks | 5.002 s |
| Private registry install | PASS | 24.666 s |
| Policy status | PASS | 1.709 s |
| Governed audit | PASS, 31 checks | 1.762 s |
| Complete critical APM path | PASS | 79.740 s |
| All four checkpoint restores | PASS | 0.107-0.319 s |

The full dry run also audited every recovery state: 10 checks for each consume/private-install
checkpoint and 31 checks for the governed checkpoint. All **102** recovery and critical audit checks
passed, and the tracked working-tree state was unchanged.
