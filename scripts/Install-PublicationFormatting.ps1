[CmdletBinding()]
param(
    [switch]$SkipApplications,
    [switch]$SkipWps
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$sourceSkill = Join-Path $repoRoot 'codex/skills/format-submission-manuscript'
$codexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME '.codex' }
$targetSkill = Join-Path $codexHome 'skills/format-submission-manuscript'
$runtime = Join-Path $codexHome 'runtimes/publication-formatting'

function Test-Command([string]$Name) {
    return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

function Install-WingetPackage([string]$Id) {
    $installed = winget list --id $Id --exact --accept-source-agreements 2>$null | Select-String -SimpleMatch $Id
    if (-not $installed) {
        Write-Host "Installing missing official package: $Id"
        winget install --id $Id --exact --accept-package-agreements --accept-source-agreements --silent --disable-interactivity
        if ($LASTEXITCODE -ne 0) { throw "winget failed for $Id" }
    }
    else {
        Write-Host "Already installed: $Id"
    }
}

if (-not (Test-Path -LiteralPath $sourceSkill -PathType Container)) {
    throw "Skill source is missing: $sourceSkill"
}

if (-not $SkipApplications) {
    if (-not (Test-Command 'winget')) { throw 'winget is required to install missing publication tools on Windows.' }
    Install-WingetPackage 'JohnMacFarlane.Pandoc'
    Install-WingetPackage 'TheDocumentFoundation.LibreOffice'
    $wpsRegistered = Test-Path -LiteralPath 'Registry::HKEY_CLASSES_ROOT\KWPS.Application\CLSID'
    if (-not $SkipWps -and -not $wpsRegistered) { Install-WingetPackage 'Kingsoft.WPSOffice.CN' }
    elseif ($wpsRegistered) { Write-Host 'WPS automation is already registered.' }
}

$pythonCandidates = @(
    (Join-Path $HOME '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'),
    (Get-Command python.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -First 1),
    (Get-Command py.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -First 1)
) | Where-Object { $_ -and (Test-Path -LiteralPath $_ -PathType Leaf) }
if (-not $pythonCandidates) { throw 'A real Python 3 runtime is required; Windows Store launcher aliases are not sufficient.' }
$python = $pythonCandidates[0]

if (-not (Test-Path -LiteralPath (Join-Path $runtime 'Scripts/python.exe') -PathType Leaf)) {
    & $python -m venv $runtime
    if ($LASTEXITCODE -ne 0) { throw 'Could not create the publication-formatting Python runtime.' }
}
$runtimePython = Join-Path $runtime 'Scripts/python.exe'
& $runtimePython -m pip install --disable-pip-version-check --requirement (Join-Path $sourceSkill 'requirements.txt')
if ($LASTEXITCODE -ne 0) { throw 'Could not install Python dependencies.' }

[System.IO.Directory]::CreateDirectory($targetSkill) | Out-Null
Copy-Item -Path (Join-Path $sourceSkill '*') -Destination $targetSkill -Recurse -Force

$formatter = Join-Path $targetSkill 'scripts/submission_formatter.py'
& $runtimePython $formatter doctor --self-test
if ($LASTEXITCODE -ne 0) { throw 'Publication formatter doctor failed.' }

Write-Host "Installed Codex skill: $targetSkill"
Write-Host 'Microsoft Word was not installed or licensed by this script. Genuine Word is enabled only when already present.'
Write-Host 'Restart Codex, then confirm format-submission-manuscript appears in /skills.'
