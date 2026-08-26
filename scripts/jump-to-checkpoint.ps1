[CmdletBinding()]
param(
  [Parameter(Mandatory)]
  [ValidateSet("consume-single", "consume-manifest", "govern-private", "govern-policy")]
  [string]$Name
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$liveRoot = Join-Path $repoRoot ".demo-live"

$checkpoint = switch ($Name) {
  "consume-single" {
    @{
      Source = "reference\consume-single"
      Destination = "consume-checkout"
      RemovePolicy = $false
    }
  }
  "consume-manifest" {
    @{
      Source = "reference\consume-checkout"
      Destination = "consume-checkout"
      RemovePolicy = $false
    }
  }
  "govern-private" {
    @{
      Source = "reference\governed-checkout"
      Destination = "governed-checkout"
      RemovePolicy = $true
    }
  }
  "govern-policy" {
    @{
      Source = "reference\governed-checkout"
      Destination = "governed-checkout"
      RemovePolicy = $false
    }
  }
}

$source = Join-Path $repoRoot $checkpoint.Source
$destination = Join-Path $liveRoot $checkpoint.Destination

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

if ($checkpoint.RemovePolicy) {
  Remove-Item -LiteralPath (Join-Path $destination "apm-policy.yml") -ErrorAction SilentlyContinue
}

Write-Host "Checkpoint '$Name' restored to $destination"
