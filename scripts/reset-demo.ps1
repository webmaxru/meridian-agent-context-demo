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

$templatePath = Join-Path $liveRoot "quarantine\refund-helper\SKILL.template.md"
$unsafePath = Join-Path $liveRoot "quarantine\refund-helper\SKILL.md"
$template = Get-Content -LiteralPath $templatePath -Raw
$unsafe = $template.Replace("{{BIDI_RLO}}", [string][char]0x202E)
[System.IO.File]::WriteAllText($unsafePath, $unsafe, [System.Text.UTF8Encoding]::new($false))
Remove-Item -LiteralPath $templatePath

Write-Host "Demo reset: $liveRoot"
Write-Host "Open this folder in VS Code, then start in .demo-live\meridian-checkout."
