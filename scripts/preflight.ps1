[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$reference = Join-Path $repoRoot "reference\meridian-checkout"
$expectedVersion = "0.28.0"

Push-Location $repoRoot
try {
  $trackedStatusBefore = (& git status --short --untracked-files=no | Out-String).Trim()

  $versionOutput = (& apm --version 2>&1 | Out-String).Trim()
  if ($LASTEXITCODE -ne 0 -or $versionOutput -notmatch [regex]::Escape($expectedVersion)) {
    throw "Expected APM $expectedVersion, got: $versionOutput"
  }

  & git ls-remote --exit-code `
    "https://github.com/webmaxru/meridian-agent-context-demo.git" `
    "refs/tags/v1.0.0" | Out-Null
  if ($LASTEXITCODE -ne 0) {
    throw "Cannot resolve the public v1.0.0 demo release."
  }

  & apm audit --file ".\registry\skills\secure-payment-review\SKILL.md" | Out-Null
  if ($LASTEXITCODE -ne 0) {
    throw "The released skill did not pass the APM file scan."
  }

  Push-Location $reference
  try {
    & apm install | Out-Null
    if ($LASTEXITCODE -ne 0) {
      throw "The reference install failed."
    }

    & apm audit --ci --policy ".\apm-policy.yml" --no-fail-fast | Out-Null
    if ($LASTEXITCODE -ne 0) {
      throw "The reference policy audit failed."
    }
  }
  finally {
    Pop-Location
  }

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
  Write-Host "Release: v1.0.0 is reachable"
  Write-Host "Reference: install + 31-check audit passed"
  Write-Host "Workspace: .demo-live reset to the opening state"
}
finally {
  Pop-Location
}
