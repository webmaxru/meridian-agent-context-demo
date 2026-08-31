# Build a Supply Chain for Agent Context - Full Talk Track

**Speaker:** Maxim Salnikov, AI-Native Solution Engineer, Microsoft
**Duration:** 30 minutes, including questions and recovery buffer
**Target spoken/demo content:** about 25 minutes

Stage directions are in brackets. Quoted prose is intended to be delivered nearly verbatim.

## 00:00-01:20 - Slide 1: the supply-chain gap

[Show slide 1.]

> Good morning. I want to start with an uncomfortable equivalence.
>
> If I put an executable from an unknown repository into my build, everyone knows what to ask. Who
> published it? Which version is it? Can I download the same thing again? Can CI stop an unapproved
> change?
>
> Now replace that executable with a Markdown file called `SKILL.md`.
>
> That file does not ship inside the production application. But it can tell an agent how to write
> code, review a payment change, generate tests, or prepare a release. It behaves more like a build
> instruction than ordinary documentation.
>
> Application tests protect the code that has already been written. Agent-context controls protect
> the instructions that will produce and review the next change.
>
> Meridian, our fictional fintech, currently copies these files between agent folders. In the next
> 25 minutes, we will give that shared context a known owner, a version, a content fingerprint, and a
> required check before merge.

[Pause on the four-word visual.]

> Owner. Version. Hash. Gate. Those are the four proofs we want by the end.

## 01:20-02:35 - Slide 2: what APM does

[Advance to slide 2.]

> The tool we will use is Agent Package Manager, or APM.
>
> I am deliberately not going to spend our time installing the CLI. That path is short and
> well-documented. Let us jump directly to the problem it solves.
>
> APM gives us two simple capabilities: restore the team's agent environment and verify that nobody
> changed it unexpectedly.
>
> `apm.yml` is the team's list of required context. The lockfile is the receipt showing exactly what
> was resolved. APM then places the files where each agent expects to find them. An audit compares
> the list, the receipt, the installed files, and the organization's policy.
>
> The manageable assets are not only skills. They include skills, prompts, instructions, plugins,
> and MCP servers.
>
> One important limit: APM does not prove that a skill contains good advice. Meridian's reviewers do
> that. APM proves that everyone received the reviewed version and that it was not silently replaced.

## 02:35-03:15 - Slide 3: consuming APM

[Advance to slide 3.]

> We start as consumers.
>
> We will solve three increasingly larger problems. First, one developer needs a safer alternative
> to copying a file. Second, the whole team needs the same context across three agents. Third, a new
> machine must be able to reproduce the same result tomorrow.

[Switch to VS Code. Show `.demo-live/consume-checkout/src/refund.ts`.]

## 03:15-05:45 - Demo: install one released skill

[State the challenge before touching the terminal.]

> The first challenge is simple: Lena found a useful skill on the internet. She can copy
> `SKILL.md` into the repository, but the copied file does not explain which release she selected or
> how the team can obtain it again.
>
> This is `meridian-checkout`. Lena uses GitHub Copilot, Omar uses Claude Code, and Priya uses
> Cursor.
>
> We want the convenience of trying one skill without losing its source and version. We will install
> one released skill from `webmaxru/ai-native-dev`.

[In the terminal, run:]

```powershell
Set-Location .\.demo-live\consume-checkout
apm init --yes --target copilot
```

> Initialization creates the dependency list and says that this project uses Copilot. It does not
> install a skill yet.

[Run:]

```powershell
apm install 'webmaxru/ai-native-dev/skills/agent-package-manager#v1.9.0'
```

[If the install exceeds 30 seconds: press Ctrl+C, return to the repository root, restore
`consume-single`, return to `.demo-live/consume-checkout`, show
`demo/fallback/01-consume-single.txt`, and continue at the generated manifest.]

> Read this coordinate from left to right. It names the owner and repository, the path to one skill,
> and the release that Lena selected.
>
> The quotes are intentional. They ensure the version pin stays part of the package coordinate in
> shells where a hash sign can start a comment.

[When output appears, point at `#v1.9.0 @d04f0b01` and `.agents/skills/`.]

> APM updated `apm.yml`; it resolved the release to commit `d04f0b01`; and it deployed the skill to
> Copilot's shared skills path.
>
> The application does not import this Markdown file. Copilot reads it when helping with future
> changes. The useful result is that the repository now explains exactly where that shared
> instruction came from.

[Open the generated `apm.yml`.]

> This is the first useful change: a copied file became a reviewable dependency declaration.

## 05:45-08:30 - Demo: make it a team manifest

[State the challenge before opening the manifest.]

> The second challenge is consistency. Lena solved the problem on her machine, but Omar and Priya
> still have nothing. Their agents also expect files in different folders. A wiki page telling each
> person what to copy will eventually drift.
>
> Meridian needs one shared list that can prepare all three agent environments. This is that list.

[Open `demo/snippets/apm-consume.yml`.]

[Point at `targets`.]

> The targets are Claude, Copilot, and Cursor.

[Point at the three release pins.]

> These three coordinates use `v1.9.0`. The release name is easy for a human to understand. The
> lockfile will still record the exact commit that the release resolved to.

[Point at the two full commit pins.]

> These two coordinates use a complete commit SHA. A commit is the strongest declaration because it
> cannot move to different content. The manifest can use a readable release or an exact commit; the
> lockfile records the exact commit in both cases.

[Point at the prompt dependency.]

> This is a prompt rather than a skill. It can instruct an agent to inspect versions, edit files,
> commit, push, and deploy. That is why prompts also need a known source and version: they can change
> the repository, not merely improve a chat answer.

[Run:]

```powershell
Copy-Item ..\..\demo\snippets\apm-consume.yml .\apm.yml
apm install
```

[If the install exceeds 60 seconds: press Ctrl+C, return to the repository root, restore
`consume-manifest`, return to `.demo-live/consume-checkout`, show
`demo/fallback/02-consume-manifest.txt`, and continue with deployment paths.]

> APM now resolves all five declared dependencies.

[As output completes, point at the target paths.]

> Four skills go to `.agents/skills` for Copilot and Cursor and to `.claude/skills` for Claude.
> The prompt goes to `.github/prompts` and is adapted into command files for Claude and Cursor.
>
> If you see warnings that `agent` and `name` frontmatter were dropped from those command adapters,
> that means the destination agent does not support those two fields. APM is showing the adaptation;
> the installation did not fail.
>
> The team maintains one declaration instead of three sets of copy instructions. Each agent still
> receives files in its own native location and format.

## 08:30-11:30 - Demo: make reproducibility visible

[State the challenge before running the path-listing commands.]

> The third challenge appears when a new developer clones the repository next week. The manifest
> says what the team wants, but a release name could resolve differently later, and somebody could
> manually edit one of the installed files.
>
> We need evidence of exactly what was resolved and exactly what each agent received.

[Run the path-listing commands.]

```powershell
Get-ChildItem -File -Recurse .agents\skills,.claude\skills -Filter SKILL.md |
  Resolve-Path -Relative
Get-Item .github\prompts\*.prompt.md,.claude\commands\*.md,.cursor\commands\*.md |
  Resolve-Path -Relative
```

> These are the real files that Copilot, Claude, and Cursor will read. They are the final installed
> result, not an abstract package name.

[Open `apm.lock.yaml`. Find a release-pinned package.]

> Think of the manifest as the shopping list and the lockfile as the receipt.
>
> `resolved_ref` says what we asked for. `resolved_commit` says the exact Git commit we received.
> `content_hash` is the fingerprint of the package content. `deployed_file_hashes` are fingerprints
> of the final files placed in each agent's folder.

[Find a full-SHA-pinned package.]

> Here the manifest already asked for an exact commit, so the requested reference and resolved
> commit are the same.

[Find the prompt package and its three deployed hashes.]

> The prompt is especially useful because its deployed content is adapted for each target. APM
> records the GitHub Copilot prompt and the Claude and Cursor command variants separately.
>
> Reproducibility does not require every agent to use the same file format. It requires us to know
> which transformation happened and to verify the resulting files.

[Run:]

```powershell
$before = (Get-FileHash .\apm.lock.yaml -Algorithm SHA256).Hash
apm install --frozen
$after = (Get-FileHash .\apm.lock.yaml -Algorithm SHA256).Hash
$before
$after
"LOCK_UNCHANGED=$($before -eq $after)"
```

> `--frozen` means: use the committed receipt and do not create a new resolution. We hash the
> lockfile before and after to make that visible. The two hashes are equal, so this replay did not
> change the recorded dependency state.
>
> A normal mutable install can update generated lock metadata. That is why this specific before-and-
> after frozen replay is the simple proof we show here.

[Only if the final summary says one dependency: point to `Replayed 5 package(s)`, the matching lock
hashes, and continue. If replay exceeds 20 seconds: restore `consume-manifest` from the repository
root and show `demo/fallback/03-reproducibility.txt`.]

[Run:]

```powershell
apm audit --ci --no-policy
```

> Ten consistency and integrity checks pass. No drift.
>
> This result does not tell us that the skill's advice is good. It tells us that the manifest, lock,
> and installed files agree and that nobody changed the installed context behind our back.
>
> We have finished the consumer half: the team has one dependency list, one exact resolution, and a
> repeatable environment for three agents.

## 11:30-12:15 - Slide 4: governing APM

[Return to slide 4.]

> Consumption solved consistency. But consistent does not automatically mean trusted. The whole
> team could consistently install the wrong thing.
>
> Meridian now needs to answer two plain questions: which sources are allowed for payment work, and
> can a developer skip the check?
>
> We will use a company-owned source, a blocking policy, and a required CI audit.

[Switch back to VS Code.]

## 12:15-15:45 - Demo: private company registry

[State the challenge before showing the registry.]

> The fourth challenge is trust. A generic public skill can be useful, but Meridian's payment rules
> are company policy. The team needs to know who owns those rules and who reviewed them.

[Show `.demo-live/governed-checkout/src/refund.ts`.]

> This small refund function shows why. It represents money as a plain number, logs the card number,
> ignores the available idempotency identifier, and does not explain what happens when the payment
> provider times out. Those are not formatting preferences. They can cause financial loss or expose
> sensitive data.

[Show the authenticated private repository page or the local
`meridian-agent-context-registry/skills/secure-payment-review/SKILL.md`.]

> This is Meridian's reviewed skill catalog. It lives in a separate private repository, and the
> `v1.0.0` release contains the `secure-payment-review` skill.
>
> The skill gives an agent five concrete checks: safe money representation, idempotent retries, no
> sensitive logging, valid payment-state transitions, and careful handling of unknown outcomes.
> Its metadata names Meridian Platform Engineering and the platform-security owner.
>
> Private does not automatically mean safe. The trust comes from ownership, review, and a controlled
> release. APM will preserve the reviewed result after that decision has been made.

[Move to the governed workspace.]

```powershell
Set-Location ..\..
Set-Location .\.demo-live\governed-checkout
```

> This project already names the three agent targets, but it does not yet declare the payment-review
> skill. It has no lockfile and no source policy.
>
> Because the registry is private, APM needs a GitHub credential to read it. Preflight loaded a
> session-only credential without printing it. The package declaration contains only the repository
> address; it does not contain the secret.

[Run:]

```powershell
apm install 'webmaxru/meridian-agent-context-registry/skills/secure-payment-review#v1.0.0'
```

[If the install exceeds 40 seconds: press Ctrl+C, return to the repository root, restore
`govern-private`, return to `.demo-live/governed-checkout`, show
`demo/fallback/04-private-registry.txt`, and continue at the manifest and lockfile.]

[Point at the output.]

> The human-readable `v1.0.0` release resolves to exact commit `5b105da7`. APM then puts the reviewed
> skill in the locations used by the configured agents.
>
> If APM prints a clone retry, it is only changing the way it downloads the repository. The selected
> release and verified content do not change.

[Open the generated manifest and lockfile.]

> The lock records the resolved commit, the package fingerprint, and the fingerprints of both
> installed copies. We can now trace this private skill back to the reviewed release.

## 15:45-19:30 - Demo: blocking sourcing policy

[State the challenge before copying the policy.]

> The fifth challenge is permission. Meridian now has an approved private registry, but nothing yet
> stops a developer from installing a different payment skill from an arbitrary public repository.
>
> The lockfile answers, "What did we install?" It does not answer, "Was this source allowed?" That
> second question belongs to policy.

[Run:]

```powershell
Copy-Item ..\..\demo\snippets\apm-policy.yml .\apm-policy.yml
```

[Open `apm-policy.yml`.]

> This policy is small enough to read completely.
>
> `enforcement: block` means a violation fails instead of producing a warning.
> `fetch_failure: block` means that if APM cannot load the policy or verify the source, the safe
> answer is no. A network problem does not become permission.
>
> The allowlist contains the Meridian registry and the packages beneath it. Any other source is
> outside the approved boundary.
>
> The final rule requires a version constraint. A moving branch such as `main` is not precise enough
> for this governed project.

[Run:]

```powershell
apm policy status --policy-source .\apm-policy.yml --check
```

> This confirms that APM found the policy and that violations will block.

[Run:]

```powershell
apm audit --ci --policy .\apm-policy.yml --no-fail-fast
```

> The audit now checks two groups of facts. First, do the manifest, lockfile, package, and installed
> files agree? Second, does the dependency come from an allowed source with an acceptable pin?
>
> Thirty-one checks pass. This is the exact agent environment that Meridian is willing to accept.

[If policy status or audit exceeds 10 seconds: restore `govern-policy` from the repository root,
return to `.demo-live/governed-checkout`, and show `demo/fallback/05-policy-audit.txt`.]

## 19:30-24:30 - Demo: the required CI gate

[State the challenge before opening the workflow.]

> The sixth challenge is enforcement. A developer can forget or choose not to run a local audit.
> A rule that depends on everybody remembering a command is not a gate.
>
> There is another important point. The application build protects the code already written. This
> audit protects the shared instructions that will guide the next code change.
>
> A pull request might leave `refund.ts` untouched but replace `secure-payment-review` with an unsafe
> instruction. The application could still compile and every unit test could pass. Without a context
> check, the poisoned instruction would be waiting for the next developer's agent.

[Open `.github/workflows/apm-supply-chain.yml`.]

> This workflow has read-only repository contents permission. The job targets the protected
> `meridian-registry` environment, so a designated reviewer must approve access before its encrypted
> `MERIDIAN_REGISTRY_PAT` secret is available. The credential is then scoped only to the audit step
> as APM's expected environment variable.
>
> In simpler terms: CI can read the public repository immediately, but it receives the private-
> registry credential only after an approved person allows that job to use it.

[Point at the action pins.]

> We also pin the audit machinery itself. Checkout has an exact commit. The APM action has an exact
> commit. The APM CLI version is explicitly `0.28.0`. The check should not silently change because
> an action tag or default moved.

[Point at `setup-only: true`.]

> `setup-only` is the most important line to explain clearly. This workflow does not reinstall or
> execute the payment skill. It installs only the APM command-line tool.
>
> We want CI to inspect the files exactly as they arrived in the proposed commit. If installation
> happened first, it could replace a tampered skill with a clean copy and hide the evidence before
> the audit saw it.
>
> So the sequence is: check out the proposed commit, install only the auditor, and compare the
> manifest, lockfile, policy, source, and installed skill files without repairing anything.

[Point at the two commands.]

> The first command confirms that the required policy exists and can be loaded. The second command
> performs the complete audit and reports every problem instead of stopping after the first one.

[Open `.github/CODEOWNERS`.]

> CODEOWNERS means that a normal contributor cannot quietly remove this workflow or weaken the
> policy without the responsible owner reviewing that change.

[Switch to the successful GitHub Actions `audit` job.]

> This is the same audit on a clean GitHub runner. It proves that the result is not dependent on my
> laptop or on files left over from the demo.
>
> No agent is running in this workflow, and the application does not need the skill to compile. The
> purpose of this job is narrower: protect the repository-managed agent environment that developers
> will use for future work.
>
> If Meridian later adds a CI step that actually runs an agent to generate tests or review payment
> changes, that job would first restore the exact locked skill and then run the agent. In today's
> demo, we are only proving and governing the input.

[If GitHub does not load in five seconds: remain in the pinned workflow and show
`demo/fallback/06-required-gate.txt`.]

[Switch to branch protection.]

> A successful workflow is still only a report until repository rules require it.
>
> Here, `audit` is a required status. A pull request cannot merge until it passes. The pull request
> also needs an approval and CODEOWNERS review. Direct pushes and force pushes are disabled, so an
> ordinary contributor cannot simply go around the pull request.
>
> The precise promise is simple: an ordinary contributor cannot merge a changed agent environment
> without the audit and owning review. Repository administrators remain the ultimate trust boundary
> because administrators can change repository settings.

[If asked about public forks: GitHub does not expose the private-registry environment secret to fork
workflows. This demo intentionally uses same-repository branches; a maintainer must recreate a
reviewed fork change on a trusted branch before it can satisfy `audit`.]
>
> That is why the consumer repository is public in this conference setup while the registry is
> private. This arrangement lets us demonstrate a real protected merge gate while keeping the
> company-owned skill source private.

## 24:30-25:00 - Slide 5: close

[Return to slide 5.]

> We started with a friendly-looking Markdown file and four unanswered questions.
>
> We did not make the refund service depend on Markdown at runtime. We made the shared development
> environment explicit and reviewable.
>
> The context now has an owner, a version, a fingerprint, and a required gate before merge.
>
> Application tests protect today's committed code. This supply chain protects the instructions that
> will help produce tomorrow's code.
>
> The QR code is my LinkedIn. The other links take you to the APM repository, the documentation, and
> the interactive book. Thank you.

## 25:00-30:00 - Questions

[Leave slide 5 visible.]

If no question arrives immediately, seed with:

> A useful place to start is one skill that people already copy between repositories. Ask four
> questions: who owns it, which version do we use, can everybody restore the same files, and can an
> unreviewed change merge? Solve those four questions before trying to govern every agent primitive
> in the company.
