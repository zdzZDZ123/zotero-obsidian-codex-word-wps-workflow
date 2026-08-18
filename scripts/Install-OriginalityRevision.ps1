[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$sourceSkill = Join-Path $repoRoot 'codex/skills/revise-originality-with-evidence'
$codexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME '.codex' }
$targetSkill = Join-Path $codexHome 'skills/revise-originality-with-evidence'
$runtime = Join-Path $codexHome 'runtimes/originality-revision'

if (-not (Test-Path -LiteralPath $sourceSkill -PathType Container)) {
    throw "Skill source is missing: $sourceSkill"
}

$pythonCandidates = @(
    (Join-Path $HOME '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'),
    (Get-Command python.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -First 1),
    (Get-Command py.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -First 1)
) | Where-Object { $_ -and (Test-Path -LiteralPath $_ -PathType Leaf) }
if (-not $pythonCandidates) {
    throw 'A real Python 3 runtime is required; Windows Store launcher aliases are not sufficient.'
}
$python = $pythonCandidates[0]

if (-not (Test-Path -LiteralPath (Join-Path $runtime 'Scripts/python.exe') -PathType Leaf)) {
    & $python -m venv $runtime
    if ($LASTEXITCODE -ne 0) { throw 'Could not create the originality-revision Python runtime.' }
}
$runtimePython = Join-Path $runtime 'Scripts/python.exe'
& $runtimePython -m pip install --disable-pip-version-check --requirement (Join-Path $sourceSkill 'requirements.txt')
if ($LASTEXITCODE -ne 0) { throw 'Could not install originality-revision dependencies.' }

[System.IO.Directory]::CreateDirectory($targetSkill) | Out-Null
Copy-Item -Path (Join-Path $sourceSkill '*') -Destination $targetSkill -Recurse -Force

$helper = Join-Path $targetSkill 'scripts/originality_revision.py'
& $runtimePython $helper doctor --self-test
if ($LASTEXITCODE -ne 0) { throw 'Originality revision doctor failed.' }

Write-Host "Installed Codex skill: $targetSkill"
Write-Host 'Processing is local-only. This installer does not install, log in to, or bypass any commercial similarity service.'
Write-Host 'Restart Codex, then confirm revise-originality-with-evidence appears in /skills.'
