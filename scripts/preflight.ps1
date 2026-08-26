[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$consumeReference = Join-Path $repoRoot "reference\consume-checkout"
$governedReference = Join-Path $repoRoot "reference\governed-checkout"
$expectedVersion = "0.28.0"

Push-Location $repoRoot
try {
  $trackedStatusBefore = (& git status --short --untracked-files=no | Out-String).Trim()

  $versionOutput = (& apm --version 2>&1 | Out-String).Trim()
  if ($LASTEXITCODE -ne 0 -or $versionOutput -notmatch [regex]::Escape($expectedVersion)) {
    throw "Expected APM $expectedVersion, got: $versionOutput"
  }

  if ([string]::IsNullOrWhiteSpace($env:GITHUB_APM_PAT)) {
    $tokenOutput = (& gh auth token 2>&1 | Out-String).Trim()
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($tokenOutput)) {
      throw "GitHub authentication is required for Meridian's private registry. Run 'gh auth login'."
    }
    $env:GITHUB_APM_PAT = $tokenOutput
    $tokenOutput = $null
  }

  $demoVisibility = (& gh repo view "webmaxru/meridian-agent-context-demo" --json visibility --jq ".visibility" 2>&1 | Out-String).Trim()
  if ($LASTEXITCODE -ne 0 -or $demoVisibility -ne "PUBLIC") {
    throw "Expected webmaxru/meridian-agent-context-demo to be PUBLIC, got: $demoVisibility"
  }

  $registryVisibility = (& gh repo view "webmaxru/meridian-agent-context-registry" --json visibility --jq ".visibility" 2>&1 | Out-String).Trim()
  if ($LASTEXITCODE -ne 0 -or $registryVisibility -ne "PRIVATE") {
    throw "Expected webmaxru/meridian-agent-context-registry to be PRIVATE, got: $registryVisibility"
  }

  & gh release view "v1.0.0" --repo "webmaxru/meridian-agent-context-registry" --json tagName | Out-Null
  if ($LASTEXITCODE -ne 0) {
    throw "Cannot resolve Meridian's private registry release v1.0.0."
  }

  & git ls-remote --exit-code `
    "https://github.com/webmaxru/ai-native-dev.git" `
    "refs/tags/v1.9.0" | Out-Null
  if ($LASTEXITCODE -ne 0) {
    throw "Cannot resolve the public ai-native-dev v1.9.0 release."
  }

  Push-Location $consumeReference
  try {
    $lockHashBefore = (Get-FileHash -LiteralPath ".\apm.lock.yaml" -Algorithm SHA256).Hash
    & apm install --frozen | Out-Null
    if ($LASTEXITCODE -ne 0) {
      throw "The consuming reference frozen install failed."
    }
    $lockHashAfter = (Get-FileHash -LiteralPath ".\apm.lock.yaml" -Algorithm SHA256).Hash
    if ($lockHashAfter -ne $lockHashBefore) {
      throw "The consuming reference lockfile changed during frozen replay."
    }
    & apm audit --ci --no-policy | Out-Null
    if ($LASTEXITCODE -ne 0) {
      throw "The consuming reference audit failed."
    }
  }
  finally {
    Pop-Location
  }
  Remove-Item -LiteralPath (Join-Path $consumeReference "apm_modules") -Recurse -Force -ErrorAction SilentlyContinue

  Push-Location $governedReference
  try {
    & apm install --frozen | Out-Null
    if ($LASTEXITCODE -ne 0) {
      throw "The governed reference frozen install failed."
    }
    & apm audit --ci --policy ".\apm-policy.yml" --no-fail-fast | Out-Null
    if ($LASTEXITCODE -ne 0) {
      throw "The governed reference policy audit failed."
    }
  }
  finally {
    Pop-Location
  }
  Remove-Item -LiteralPath (Join-Path $governedReference "apm_modules") -Recurse -Force -ErrorAction SilentlyContinue

  & (Join-Path $PSScriptRoot "reset-demo.ps1")
  if ($LASTEXITCODE -ne 0) {
    throw "The live workspace reset failed."
  }

  $trackedStatusAfter = (& git status --short --untracked-files=no | Out-String).Trim()
  if ($trackedStatusAfter -ne $trackedStatusBefore) {
    throw "Preflight changed tracked files. Inspect git status before presenting."
  }

  Write-Host ""
  Write-Host "Preflight PASS" -ForegroundColor Green
  Write-Host "APM: $versionOutput"
  Write-Host "Public source: ai-native-dev v1.9.0 is reachable"
  Write-Host "Private source: meridian-agent-context-registry v1.0.0 authenticated (credential not printed)"
  Write-Host "Consume reference: frozen replay + audit passed"
  Write-Host "Govern reference: frozen replay + policy audit passed"
  Write-Host "Workspace: .demo-live reset to both opening states"
}
finally {
  Pop-Location
}
