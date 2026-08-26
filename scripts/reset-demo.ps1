[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$source = Join-Path $repoRoot "demo\start"
$liveRoot = Join-Path $repoRoot ".demo-live"

if (-not $liveRoot.StartsWith($repoRoot + [System.IO.Path]::DirectorySeparatorChar)) {
  throw "Refusing to reset a path outside the demo repository: $liveRoot"
}

if (Test-Path -LiteralPath $liveRoot) {
  Remove-Item -LiteralPath $liveRoot -Recurse -Force
}

Copy-Item -LiteralPath $source -Destination $liveRoot -Recurse

Write-Host "Demo reset: $liveRoot"
Write-Host "Start in .demo-live\consume-checkout, then continue in .demo-live\governed-checkout."
