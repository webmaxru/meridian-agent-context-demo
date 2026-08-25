[CmdletBinding()]
param(
  [Parameter(Mandatory)]
  [ValidateSet("installed", "governed")]
  [string]$Name
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$source = Join-Path $repoRoot "reference\meridian-checkout"
$liveRoot = Join-Path $repoRoot ".demo-live"
$destination = Join-Path $liveRoot "meridian-checkout"

if (-not (Test-Path -LiteralPath $source)) {
  throw "Reference checkpoint is missing: $source"
}

if (-not $destination.StartsWith($repoRoot + [System.IO.Path]::DirectorySeparatorChar)) {
  throw "Refusing to replace a path outside the demo repository: $destination"
}

if (-not (Test-Path -LiteralPath $liveRoot)) {
  New-Item -ItemType Directory -Path $liveRoot | Out-Null
}

if (Test-Path -LiteralPath $destination) {
  Remove-Item -LiteralPath $destination -Recurse -Force
}

Copy-Item -LiteralPath $source -Destination $destination -Recurse

if ($Name -eq "installed") {
  Remove-Item -LiteralPath (Join-Path $destination "apm-policy.yml") -ErrorAction SilentlyContinue
}

Write-Host "Checkpoint '$Name' restored to $destination"
