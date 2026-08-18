[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Arguments
)

$ErrorActionPreference = 'Stop'
$codexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME '.codex' }
$python = Join-Path $codexHome 'runtimes/originality-revision/Scripts/python.exe'
$helper = Join-Path $codexHome 'skills/revise-originality-with-evidence/scripts/originality_revision.py'
if (-not (Test-Path -LiteralPath $python -PathType Leaf) -or -not (Test-Path -LiteralPath $helper -PathType Leaf)) {
    throw 'revise-originality-with-evidence is not installed. Run scripts/Install-OriginalityRevision.ps1 first.'
}
& $python $helper @Arguments
exit $LASTEXITCODE
