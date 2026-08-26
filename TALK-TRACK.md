# Build a Supply Chain for Agent Context - Full Talk Track

**Speaker:** Maxim Salnikov, AI-Native Solution Engineer, Microsoft
**Duration:** 30 minutes, including questions and recovery buffer
**Target spoken/demo content:** about 25 minutes

Stage directions are in brackets. Quoted prose is intended to be delivered nearly verbatim.

## 00:00-01:20 - Slide 1: the supply-chain gap

[Show slide 1.]

> Good morning. I want to start with an uncomfortable equivalence.
>
> If I download an executable from an unknown repository and put it into my build, everyone in this
> room knows what questions to ask. Who published it? Which version is it? Can I reproduce the
> resolution? Has its integrity been validated? Can continuous integration stop an unapproved
> change?
>
> Now replace that executable with a Markdown file called `SKILL.md`.
>
> That file can influence an agent that reads source code, edits files, calls tools, and prepares a
> pull request. But teams still copy these files from the internet, drop them into three different
> agent folders, and treat the result as configuration.
>
> Meridian, our fictional fintech, already has a supply chain for application dependencies. In the
> next 25 minutes, we will build the missing one for agent context. We will give it a source, a
> version, a resolved commit, hashes for what reaches each harness, and a gate before merge.

[Pause on the four-word visual.]

> Owner. Version. Hash. Gate. Those are the four proofs we want by the end.

## 01:20-02:35 - Slide 2: what APM does

[Advance to slide 2.]

> The tool we will use is Agent Package Manager, or APM.
>
> I am deliberately not going to spend our time installing the CLI. That path is short and
> well-documented. I want to jump directly to the point where APM changes the engineering model.
>
> APM treats agent context as a packageable dependency. It can source and install it. It records the
> exact resolution in a lockfile. It deploys the same source into the native locations expected by
> different harnesses. And it can audit that result against organization policy in continuous
> integration.
>
> The manageable assets are not only skills. They include skills, prompts, instructions, plugins,
> and MCP servers.
>
> Today we will use skills and a prompt because they make the filesystem result easy to see. The
> same supply-chain questions apply to every asset type: where did it come from, what did it resolve
> to, and is it allowed here?

## 02:35-03:15 - Slide 3: consuming APM

[Advance to slide 3.]

> We start as consumers.
>
> First, one developer installs one released skill. Then the team turns that experiment into a
> shared manifest containing several skills and a prompt. Finally, we inspect the lock and replay it
> without changing a byte.
>
> The progression matters: addressable package, declared team intent, immutable evidence.

[Switch to VS Code. Show `.demo-live/consume-checkout/src/refund.ts`.]

## 03:15-05:45 - Demo: install one released skill

> This is `meridian-checkout`. Lena uses GitHub Copilot, Omar uses Claude Code, and Priya uses
> Cursor. They want reusable expertise, but they do not want a folder of copied context that nobody
> can explain six weeks later.
>
> We begin with Lena trying one public skill from `webmaxru/ai-native-dev`. The repository has a
> stable `v1.9.0` release. We will address one skill below that repository instead of installing the
> entire source tree.

[In the terminal, run:]

```powershell
Set-Location .\.demo-live\consume-checkout
apm init --yes --target copilot
```

> Initialization only gives this project a manifest and a target. The interesting command is the
> next one.

[Run:]

```powershell
apm install 'webmaxru/ai-native-dev/skills/agent-package-manager#v1.9.0'
```

[If the install exceeds 30 seconds: press Ctrl+C, return to the repository root, restore
`consume-single`, return to `.demo-live/consume-checkout`, show
`demo/fallback/01-consume-single.txt`, and continue at the generated manifest.]

> Read this coordinate from left to right: owner and repository, the path of one independently
> addressable skill, and the released version after the hash sign.
>
> The quotes are intentional. They ensure the version pin stays part of the package coordinate in
> shells where a hash sign can start a comment.

[When output appears, point at `#v1.9.0 @d04f0b01` and `.agents/skills/`.]

> APM updated `apm.yml`; it resolved the release to commit `d04f0b01`; and it deployed the skill to
> Copilot's shared skills path.
>
> Nothing here asks us to trust a copied file name. The project now carries the dependency
> declaration that explains where this context came from.

[Open the generated `apm.yml`.]

> This is the first useful change: context moved from an undocumented folder to reviewable project
> intent.

## 05:45-08:30 - Demo: make it a team manifest

[Open `demo/snippets/apm-consume.yml`.]

> One developer proving a skill is useful is not yet a team environment.
>
> Meridian wants the same context for all three harnesses, and it wants more than one asset. This is
> the prepared team manifest.

[Point at `targets`.]

> The targets are Claude, Copilot, and Cursor.

[Point at the three release pins.]

> These three coordinates use `v1.9.0`. A release tag is readable to a human. It communicates the
> producer's version.

[Point at the two full commit pins.]

> These two use the complete commit SHA. A Git object coordinate is immutable. We can choose the
> amount of readability or immutability we need in the manifest, and the lockfile will capture the
> exact resolution for both.

[Point at the prompt dependency.]

> This is also not skills-only. The same manifest installs a prompt file as a packageable context
> primitive.

[Run:]

```powershell
Copy-Item ..\..\demo\snippets\apm-consume.yml .\apm.yml
apm install
```

[If the install exceeds 60 seconds: press Ctrl+C, return to the repository root, restore
`consume-manifest`, return to `.demo-live/consume-checkout`, show
`demo/fallback/02-consume-manifest.txt`, and continue with deployment paths.]

> APM now resolves five dependencies from the same external repository.

[As output completes, point at the target paths.]

> Four skills go to `.agents/skills` for Copilot and Cursor and to `.claude/skills` for Claude.
> The prompt goes to `.github/prompts` and is adapted into command files for Claude and Cursor.
>
> If you see warnings that `agent` and `name` frontmatter were dropped from those command adapters,
> that is the tool making target compatibility explicit. It is not a failed install.
>
> One source declaration, native output for three harnesses. The team no longer maintains three
> hand-edited copies.

## 08:30-11:30 - Demo: make reproducibility visible

[Run the path-listing commands.]

```powershell
Get-ChildItem -File -Recurse .agents\skills,.claude\skills -Filter SKILL.md |
  Resolve-Path -Relative
Get-Item .github\prompts\*.prompt.md,.claude\commands\*.md,.cursor\commands\*.md |
  Resolve-Path -Relative
```

> These are the files the agents actually see.

[Open `apm.lock.yaml`. Find a release-pinned package.]

> The manifest is intent. This lockfile is evidence.
>
> `resolved_ref` keeps the human version. `resolved_commit` records the immutable source revision.
> `content_hash` identifies the resolved package. And `deployed_file_hashes` records what actually
> reached each harness path.

[Find a full-SHA-pinned package.]

> Here the declared reference and resolved commit are already the same full SHA.

[Find the prompt package and its three deployed hashes.]

> The prompt is especially useful because its deployed content is adapted for each target. APM
> records the GitHub Copilot prompt and the Claude and Cursor command variants separately.
>
> Reproducibility does not mean pretending every harness consumes the same shape. It means the
> transformation and its output are accounted for.

[Run:]

```powershell
$before = (Get-FileHash .\apm.lock.yaml -Algorithm SHA256).Hash
apm install --frozen
$after = (Get-FileHash .\apm.lock.yaml -Algorithm SHA256).Hash
$before
$after
"LOCK_UNCHANGED=$($before -eq $after)"
```

> Frozen replay uses the committed resolution. In this dry run, both lockfile hashes are
> identical, and the result is true. A fresh mutable install can produce a different overall
> lockfile digest because the lock includes generated metadata; equality across this frozen replay
> is the proof.

[Only if the final summary says one dependency: point to `Replayed 5 package(s)`, the matching lock
hashes, and continue. If replay exceeds 20 seconds: restore `consume-manifest` from the repository
root and show `demo/fallback/03-reproducibility.txt`.]

[Run:]

```powershell
apm audit --ci --no-policy
```

> Ten consistency and integrity checks pass. No drift.
>
> We have finished the consumer half: packages are addressable, team intent is declarative, the
> resolution is exact, and every harness receives accounted-for files.

## 11:30-12:15 - Slide 4: governing APM

[Return to slide 4.]

> Consumption solves consistency. Governance answers a different question: which sources are
> acceptable for this repository, and who can merge a change?
>
> Meridian will use a private company registry, a fail-closed sourcing policy, pinned CI tooling,
> and a required `audit` status.
>
> We are going to demonstrate the complete setup. We do not need a theatrical failure to prove that
> a blocking control exists.

[Switch back to VS Code.]

## 12:15-15:45 - Demo: private company registry

[Show the authenticated private repository page or the local
`meridian-agent-context-registry/skills/secure-payment-review/SKILL.md`.]

> This is Meridian's company-owned registry. It is a separate private repository, and the
> `v1.0.0` release contains a reviewed `secure-payment-review` skill.
>
> The skill is intentionally narrow. It checks money representation, idempotency, sensitive
> logging, state transitions, and unknown payment outcomes. The metadata names Meridian Platform
> Engineering and the platform-security owner.
>
> Private does not magically mean safe. The useful change is that Meridian controls the source and
> its release process. We can now decide that only this source is acceptable for governed payment
> context.

[Move to the governed workspace.]

```powershell
Set-Location ..\..
Set-Location .\.demo-live\governed-checkout
```

> This project already names the three harness targets, but it has no dependency, no lockfile, and
> no policy.
>
> Preflight loaded a session-only GitHub credential without printing it. CI will use an encrypted
> `meridian-registry` environment secret. The package coordinate itself remains secret-free.

[Run:]

```powershell
apm install 'webmaxru/meridian-agent-context-registry/skills/secure-payment-review#v1.0.0'
```

[If the install exceeds 40 seconds: press Ctrl+C, return to the repository root, restore
`govern-private`, return to `.demo-live/governed-checkout`, show
`demo/fallback/04-private-registry.txt`, and continue at the manifest and lockfile.]

[Point at the output.]

> The private release resolves to commit `5b105da7`. APM deploys one source skill to the shared
> `.agents` path and Claude's native path.
>
> If a partial-clone message appears, APM automatically retries with a full bare clone. That is a
> transport fallback, not a supply-chain fallback; the released ref and content are still verified.

[Open the generated manifest and lockfile.]

> The package hash is `54bda7...4016`, and the lock records two deployed-file hashes. We now have
> provenance and reproducibility for a private source.

## 15:45-19:30 - Demo: blocking sourcing policy

> But a lock answers only, "What did we install?" Governance must also answer, "Were we allowed to
> install it?"

[Run:]

```powershell
Copy-Item ..\..\demo\snippets\apm-policy.yml .\apm-policy.yml
```

[Open `apm-policy.yml`.]

> This policy is small enough to read completely.
>
> `enforcement: block` makes violations fail. `fetch_failure: block` means an unavailable policy or
> source is not interpreted as permission.
>
> The allowlist names Meridian's private registry. The second pattern includes packages below the
> repository root, which is where this skill lives.
>
> And every dependency must carry a pinned constraint. A branch tip does not satisfy this project.

[Run:]

```powershell
apm policy status --policy-source .\apm-policy.yml --check
```

> Policy found. Blocking enforcement. Two effective allow patterns. No warnings.

[Run:]

```powershell
apm audit --ci --policy .\apm-policy.yml --no-fail-fast
```

> This replays the package, checks manifest-to-lock consistency, validates deployed files and
> hashes, validates content integrity, checks the source allowlist, and verifies the pin.
>
> Thirty-one checks pass. This is the state Meridian allows to merge.

[If policy status or audit exceeds 10 seconds: restore `govern-policy` from the repository root,
return to `.demo-live/governed-checkout`, and show `demo/fallback/05-policy-audit.txt`.]

## 19:30-24:30 - Demo: the required CI gate

[Open `.github/workflows/apm-supply-chain.yml`.]

> A local command is evidence, but it is not governance. A developer can skip a local command.
> Governance needs a repository boundary.
>
> This workflow has read-only repository contents permission. The job targets the protected
> `meridian-registry` environment, so a designated reviewer must approve access before its encrypted
> `MERIDIAN_REGISTRY_PAT` secret is available. The credential is then scoped only to the audit step
> as APM's expected environment variable.
>
> That approval is a deliberate decision to expose the private-registry credential to this
> pull-request job. CODEOWNERS separately prevents an ordinary contributor from merging changes to
> the workflow or policy without owner review.

[Point at the action pins.]

> Checkout is pinned to an immutable commit. The APM action is pinned to an immutable commit. And
> the CLI version is explicitly `0.28.0`; we do not inherit an older action default.

[Point at `setup-only: true`.]

> `setup-only` matters. The action installs the tool but does not run an install that could repair a
> tampered deployed file before we audit it.

[Point at the two commands.]

> First, policy must exist and load with a fresh fetch. Then the full audit runs with cache disabled
> and without stopping at the first finding.

[Open `.github/CODEOWNERS`.]

> The workflow and policy path require owning review.

[Switch to the successful GitHub Actions `audit` job.]

> This is the same 31-check result on a fresh hosted runner, including access to the separate
> private registry.

[If GitHub does not load in five seconds: remain in the pinned workflow and show
`demo/fallback/06-required-gate.txt`.]

[Switch to branch protection.]

> And this is what changes a green command into a gate.
>
> `audit` is a strict required status. Pull requests need one approval and CODEOWNERS review. Direct
> pushes and force pushes are disabled. The private-registry environment also requires approval
> before CI receives its credential. Branch deletion is disabled. Linear history and resolved
> conversations are required. Administrator enforcement is on.
>
> The precise guarantee is important: an ordinary contributor cannot merge around this audit. As
> with every repository control, administrators remain the ultimate trust boundary.

[If asked about public forks: GitHub does not expose the private-registry environment secret to fork
workflows. This demo intentionally uses same-repository branches; a maintainer must recreate a
reviewed fork change on a trusted branch before it can satisfy `audit`.]
>
> That is why the consumer repository is public in this conference setup while the registry is
> private. GitHub Free removes branch protection from private repositories. Rather than show a
> fictional control, this demo separates the private source from a consumer where the required gate
> is real and inspectable.

## 24:30-25:00 - Slide 5: close

[Return to slide 5.]

> We started with a friendly-looking Markdown file and four unanswered questions.
>
> Now the context has an owner: a reviewed public producer or Meridian's company registry.
>
> It has a version: a release tag or an explicit commit constraint.
>
> It has a hash: the resolved package and the files deployed to each harness.
>
> And it has a gate: blocking source policy and a required audit before merge.
>
> Agent context becomes a real dependency when it has an owner, a version, a hash, and a gate.
>
> The QR code is my LinkedIn. The other links take you to the APM repository, the documentation, and
> the interactive book. Thank you.

## 25:00-30:00 - Questions

[Leave slide 5 visible.]

If no question arrives immediately, seed with:

> A useful place to start is not every piece of context in the company. Pick one skill that is
> already being copied between repositories. Give it an owner and release, install it through a
> manifest, commit the lock, and make the audit required. That one path exposes the real governance
> decisions without a platform rewrite.
