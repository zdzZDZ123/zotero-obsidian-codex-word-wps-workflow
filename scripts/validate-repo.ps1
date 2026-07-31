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

$forbiddenExtensions = @('.pdf', '.epub', '.sqlite', '.db', '.xpi', '.zip', '.7z', '.dmg', '.exe', '.msi')
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

$textExtensions = @('.md', '.json', '.yaml', '.yml', '.toml', '.ps1', '.command', '.css', '.txt', '.cff')
$privatePathPatterns = @(
    '(?i)[A-Z]:\\Users\\[^\\\s]+',
    '(?i)D:\\AI project',
    '(?i)/Users/[^/\s]+/(?:Library|\.codex|Documents)'
)
$secretAssignmentPattern = '(?i)(?:bearer(?:_token)?|api[_-]?key|client[_-]?secret|password|access[_-]?token)\s*["'']?\s*[:=]\s*["''][A-Za-z0-9_./+\-=]{16,}["'']'

foreach ($file in $files | Where-Object { $textExtensions -contains $_.Extension.ToLowerInvariant() }) {
    $content = Get-Content -LiteralPath $file.FullName -Raw
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
        $null = Get-Content -LiteralPath $json.FullName -Raw | ConvertFrom-Json
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
    $firstLine = Get-Content -LiteralPath $skill.FullName -TotalCount 1
    if ($firstLine -ne '---') {
        $errors.Add("Skill front matter missing: $($skill.FullName.Substring($root.Length + 1))")
    }
}

if ($errors.Count -gt 0) {
    $errors | ForEach-Object { Write-Error $_ }
    exit 1
}

Write-Host "Validation passed: $($files.Count) files, $($skillFiles.Count) local skills, no forbidden artifacts or obvious secrets."
