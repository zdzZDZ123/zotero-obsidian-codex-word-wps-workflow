[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$FormatterArguments
)

$ErrorActionPreference = 'Stop'
$codexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $HOME '.codex' }
$formatter = Join-Path $codexHome 'skills/format-submission-manuscript/scripts/submission_formatter.py'
$runtimePython = Join-Path $codexHome 'runtimes/publication-formatting/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $formatter -PathType Leaf)) {
    throw 'format-submission-manuscript is not installed. Run scripts/Install-PublicationFormatting.ps1 first.'
}
if (-not (Test-Path -LiteralPath $runtimePython -PathType Leaf)) {
    throw 'The publication-formatting runtime is missing. Re-run the installer.'
}
& $runtimePython $formatter @FormatterArguments
exit $LASTEXITCODE
