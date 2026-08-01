[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$errors = [System.Collections.Generic.List[string]]::new()

$required = @(
    'README.md',
    'README.zh-CN.md',
    'LICENSE',
    'SECURITY.md',
    'docs/component-lock.json',
    'prompts/01-setup-obsidian.md',
    'prompts/02-setup-zotero.md',
    'prompts/03-connect-codex.md',
    'prompts/05-setup-publication-formatting.md',
    'docs/publication-formatting.md',
    'codex/skills/format-submission-manuscript/SKILL.md',
    'codex/skills/format-submission-manuscript/agents/openai.yaml',
    'codex/skills/format-submission-manuscript/references/submission.schema.json',
    'codex/skills/format-submission-manuscript/references/profile.schema.json',
    'scripts/Install-PublicationFormatting.ps1',
    'scripts/Install-PublicationFormatting-macOS.command',
    'obsidian/vault-template/AGENTS.md',
    'obsidian/vault-template/.obsidian/community-plugins.json',
    'obsidian/vault-template/.agents/skills/run-traceable-research/SKILL.md'
)

foreach ($relative in $required) {
    $path = Join-Path $root $relative
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        $errors.Add("Missing required file: $relative")
    }
}

$forbiddenExtensions = @('.pdf', '.epub', '.sqlite', '.db', '.xpi', '.zip', '.7z', '.dmg', '.exe', '.msi', '.docx', '.dotx')
$files = Get-ChildItem -LiteralPath $root -Recurse -Force -File | Where-Object {
    $_.FullName -notmatch '[\\/]\.git[\\/]'
}

foreach ($file in $files) {
    if ($forbiddenExtensions -contains $file.Extension.ToLowerInvariant()) {
        $errors.Add("Forbidden binary/data file: $($file.FullName.Substring($root.Length + 1))")
    }
}

$pluginRoot = Join-Path $root 'obsidian/vault-template/.obsidian/plugins'
if (Test-Path -LiteralPath $pluginRoot) {
    Get-ChildItem -LiteralPath $pluginRoot -Recurse -Force -File | Where-Object { $_.Name -ne 'data.json' } | ForEach-Object {
        $errors.Add("Vendored plugin code is not allowed: $($_.FullName.Substring($root.Length + 1))")
    }
}

$textExtensions = @('.md', '.json', '.yaml', '.yml', '.toml', '.ps1', '.command', '.css', '.txt', '.cff', '.py')
$privatePathPatterns = @(
    '(?i)[A-Z]:\\Users\\[^\\\s]+',
    '(?i)D:\\AI project',
    '(?i)/Users/[^/\s]+/(?:Library|\.codex|Documents)'
)
$secretAssignmentPattern = '(?i)(?:bearer(?:_token)?|api[_-]?key|client[_-]?secret|password|access[_-]?token)\s*["'']?\s*[:=]\s*["''][A-Za-z0-9_./+\-=]{16,}["'']'

foreach ($file in $files | Where-Object { $textExtensions -contains $_.Extension.ToLowerInvariant() }) {
    $content = Get-Content -LiteralPath $file.FullName -Raw -Encoding UTF8
    foreach ($pattern in $privatePathPatterns) {
        if ($content -match $pattern) {
            $errors.Add("Private absolute path pattern in: $($file.FullName.Substring($root.Length + 1))")
            break
        }
    }
    if ($content -match $secretAssignmentPattern) {
        $errors.Add("Credential-like assignment in: $($file.FullName.Substring($root.Length + 1))")
    }
}

foreach ($json in $files | Where-Object { $_.Extension -eq '.json' }) {
    try {
        $null = Get-Content -LiteralPath $json.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
    }
    catch {
        $errors.Add("Invalid JSON: $($json.FullName.Substring($root.Length + 1)): $($_.Exception.Message)")
    }
}

$skillFiles = Get-ChildItem -LiteralPath (Join-Path $root 'obsidian/vault-template/.agents/skills') -Recurse -Filter 'SKILL.md' -File
if ($skillFiles.Count -ne 5) {
    $errors.Add("Expected 5 Vault-local skills, found $($skillFiles.Count)")
}
foreach ($skill in $skillFiles) {
    $firstLine = Get-Content -LiteralPath $skill.FullName -TotalCount 1 -Encoding UTF8
    if ($firstLine -ne '---') {
        $errors.Add("Skill front matter missing: $($skill.FullName.Substring($root.Length + 1))")
    }
}

$codexSkill = Join-Path $root 'codex/skills/format-submission-manuscript/SKILL.md'
if (Test-Path -LiteralPath $codexSkill -PathType Leaf) {
    $skillContent = Get-Content -LiteralPath $codexSkill -Raw -Encoding UTF8
    if ((Get-Content -LiteralPath $codexSkill -TotalCount 1 -Encoding UTF8) -ne '---') {
        $errors.Add('Codex skill front matter is missing')
    }
    if ($skillContent -match '\[TODO|TODO:') {
        $errors.Add('Codex skill contains scaffold TODO text')
    }
    if ($skillContent -notmatch '(?m)^name: format-submission-manuscript$') {
        $errors.Add('Codex skill name does not match its directory')
    }
}

if ($errors.Count -gt 0) {
    $errors | ForEach-Object { Write-Error $_ }
    exit 1
}

Write-Host "Validation passed: $($files.Count) files, $($skillFiles.Count) local skills, no forbidden artifacts or obvious secrets."
