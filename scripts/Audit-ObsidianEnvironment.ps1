#requires -Version 5.1
<#
.SYNOPSIS
Creates a privacy-safe inventory of an Obsidian research environment.

.DESCRIPTION
The report includes application/configuration state, plugin versions and hashes,
templates, snippets, vault-local Codex skills, the Academic Research Suite
adapter version, and Git/Codex availability. It never reads note contents,
chat sessions, API keys, credentials, or full Git remote URLs.
#>

[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [string]$VaultPath = (Get-Location).Path,

    [string]$OutputDirectory,

    [string]$CodexHome = (Join-Path $HOME ".codex"),

    [switch]$NoWrite
)

$ErrorActionPreference = "Stop"
$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)

function Get-FileSha256 {
    param([Parameter(Mandatory)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $null }
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Read-JsonSafe {
    param([Parameter(Mandatory)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $null }
    return Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json
}

function Find-ObsidianExecutable {
    $candidates = @(
        (Join-Path $env:LOCALAPPDATA "Programs\Obsidian\Obsidian.exe"),
        (Join-Path $env:LOCALAPPDATA "Obsidian\Obsidian.exe"),
        (Join-Path $env:ProgramFiles "Obsidian\Obsidian.exe")
    )
    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            return (Get-Item -LiteralPath $candidate)
        }
    }
    return $null
}

function Find-CodexExecutable {
    $command = Get-Command codex.exe -ErrorAction SilentlyContinue
    if ($command -and (Test-Path -LiteralPath $command.Source -PathType Leaf)) {
        return (Get-Item -LiteralPath $command.Source)
    }
    $roots = @(
        (Join-Path $env:LOCALAPPDATA "OpenAI\Codex\bin"),
        (Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Links")
    )
    foreach ($root in $roots) {
        if (-not (Test-Path -LiteralPath $root -PathType Container)) { continue }
        $match = Get-ChildItem -LiteralPath $root -Recurse -Filter codex.exe -File -ErrorAction SilentlyContinue |
            Sort-Object LastWriteTimeUtc -Descending |
            Select-Object -First 1
        if ($match) { return $match }
    }
    return $null
}

function Get-FrontmatterValue {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$Key
    )
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $null }
    $line = Get-Content -LiteralPath $Path -Encoding UTF8 |
        Where-Object { $_ -match ("^" + [regex]::Escape($Key) + ":\s*(.+)$") } |
        Select-Object -First 1
    if (-not $line) { return $null }
    return (($line -replace ("^" + [regex]::Escape($Key) + ":\s*"), "").Trim().Trim('"'))
}

$VaultPath = [System.IO.Path]::GetFullPath($VaultPath)
$ObsidianPath = Join-Path $VaultPath ".obsidian"
if (-not (Test-Path -LiteralPath $ObsidianPath -PathType Container)) {
    throw "Not an Obsidian vault: $VaultPath"
}

if (-not $OutputDirectory) {
    $OutputDirectory = Join-Path $VaultPath "90-System\Audits"
}
$OutputDirectory = [System.IO.Path]::GetFullPath($OutputDirectory)

$appConfig = Read-JsonSafe (Join-Path $ObsidianPath "app.json")
$appearance = Read-JsonSafe (Join-Path $ObsidianPath "appearance.json")
$coreConfig = Read-JsonSafe (Join-Path $ObsidianPath "core-plugins.json")
$communityRaw = Read-JsonSafe (Join-Path $ObsidianPath "community-plugins.json")
$communityIds = @($communityRaw | ForEach-Object { [string]$_ })
$templateConfig = Read-JsonSafe (Join-Path $ObsidianPath "templates.json")
$dailyConfig = Read-JsonSafe (Join-Path $ObsidianPath "daily-notes.json")

$coreEnabled = @()
$coreDisabled = @()
if ($coreConfig) {
    foreach ($property in $coreConfig.psobject.Properties) {
        if ([bool]$property.Value) { $coreEnabled += $property.Name }
        else { $coreDisabled += $property.Name }
    }
}

$plugins = @()
$pluginsRoot = Join-Path $ObsidianPath "plugins"
if (Test-Path -LiteralPath $pluginsRoot -PathType Container) {
    foreach ($folder in (Get-ChildItem -LiteralPath $pluginsRoot -Directory | Sort-Object Name)) {
        $manifestPath = Join-Path $folder.FullName "manifest.json"
        if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) { continue }
        $manifest = Read-JsonSafe $manifestPath
        $files = @()
        foreach ($name in @("manifest.json", "main.js", "styles.css")) {
            $path = Join-Path $folder.FullName $name
            if (Test-Path -LiteralPath $path -PathType Leaf) {
                $item = Get-Item -LiteralPath $path
                $files += [ordered]@{
                    name = $name
                    bytes = $item.Length
                    sha256 = Get-FileSha256 $path
                }
            }
        }
        $plugins += [ordered]@{
            folder = $folder.Name
            id = $manifest.id
            name = $manifest.name
            version = $manifest.version
            min_app_version = $manifest.minAppVersion
            enabled = ($communityIds -contains $manifest.id)
            files = $files
        }
    }
}

$snippets = @()
$snippetRoot = Join-Path $ObsidianPath "snippets"
if (Test-Path -LiteralPath $snippetRoot -PathType Container) {
    $snippets = @(Get-ChildItem -LiteralPath $snippetRoot -File | Sort-Object Name | ForEach-Object {
        [ordered]@{
            name = $_.Name
            bytes = $_.Length
            sha256 = Get-FileSha256 $_.FullName
            enabled = ($appearance.enabledCssSnippets -contains $_.BaseName)
        }
    })
}

$themes = @()
$themeRoot = Join-Path $ObsidianPath "themes"
if (Test-Path -LiteralPath $themeRoot -PathType Container) {
    $themes = @(Get-ChildItem -LiteralPath $themeRoot -Directory | Sort-Object Name | Select-Object -ExpandProperty Name)
}

$templates = @()
$templateFolder = if ($templateConfig -and $templateConfig.folder) { [string]$templateConfig.folder } else { "99-Templates" }
$templateRoot = Join-Path $VaultPath $templateFolder
if (Test-Path -LiteralPath $templateRoot -PathType Container) {
    $templates = @(Get-ChildItem -LiteralPath $templateRoot -File -Filter *.md | Sort-Object Name | ForEach-Object {
        [ordered]@{
            name = $_.Name
            sha256 = Get-FileSha256 $_.FullName
        }
    })
}

$localSkills = @()
$skillsRoot = Join-Path $VaultPath ".agents\skills"
if (Test-Path -LiteralPath $skillsRoot -PathType Container) {
    foreach ($skillFolder in (Get-ChildItem -LiteralPath $skillsRoot -Directory | Sort-Object Name)) {
        $skillFile = Join-Path $skillFolder.FullName "SKILL.md"
        if (-not (Test-Path -LiteralPath $skillFile -PathType Leaf)) { continue }
        $localSkills += [ordered]@{
            folder = $skillFolder.Name
            name = Get-FrontmatterValue -Path $skillFile -Key "name"
            description = Get-FrontmatterValue -Path $skillFile -Key "description"
            sha256 = Get-FileSha256 $skillFile
        }
    }
}

$obsidianExe = Find-ObsidianExecutable
$codexExe = Find-CodexExecutable
$arsManifestPath = Join-Path $CodexHome "skills\academic-research-suite\manifest.json"
$arsManifest = Read-JsonSafe $arsManifestPath

$gitAvailable = $null -ne (Get-Command git.exe -ErrorAction SilentlyContinue)
$gitBranch = $null
$gitHead = $null
$gitRemoteHost = $null
if ($gitAvailable -and (Test-Path -LiteralPath (Join-Path $VaultPath ".git") -PathType Container)) {
    $gitBranch = (git -C $VaultPath branch --show-current 2>$null | Select-Object -First 1)
    $gitHead = (git -C $VaultPath rev-parse HEAD 2>$null | Select-Object -First 1)
    $remote = $null
    $remoteNames = @(git -C $VaultPath remote 2>$null)
    if ($remoteNames -contains "origin") {
        $remote = (git -C $VaultPath remote get-url origin 2>$null | Select-Object -First 1)
    }
    if ($remote) {
        if ($remote -match "^git@([^:]+):") { $gitRemoteHost = $matches[1] }
        elseif ($remote -match "^[a-zA-Z]+://([^/]+)") { $gitRemoteHost = $matches[1] }
        else { $gitRemoteHost = "configured-non-url" }
    }
}

$configFiles = @()
foreach ($name in @(
    "app.json",
    "appearance.json",
    "core-plugins.json",
    "community-plugins.json",
    "templates.json",
    "daily-notes.json",
    "types.json"
)) {
    $path = Join-Path $ObsidianPath $name
    if (Test-Path -LiteralPath $path -PathType Leaf) {
        $configFiles += [ordered]@{
            name = $name
            sha256 = Get-FileSha256 $path
        }
    }
}

$report = [ordered]@{
    schema_version = 1
    generated_at = (Get-Date).ToString("o")
    privacy = "No note contents, chat sessions, credentials, tokens, device IDs, full remotes, or workspace layout are included."
    vault = [ordered]@{
        path = $VaultPath
        folders = @(Get-ChildItem -LiteralPath $VaultPath -Directory | Where-Object { $_.Name -notmatch "^\.(git|trash|claudian)$" } | Sort-Object Name | Select-Object -ExpandProperty Name)
    }
    obsidian = [ordered]@{
        executable_present = [bool]$obsidianExe
        executable_version = if ($obsidianExe) { $obsidianExe.VersionInfo.FileVersion } else { $null }
        app_config = $appConfig
        appearance = $appearance
        core_enabled = $coreEnabled
        core_disabled = $coreDisabled
        community_enabled_ids = $communityIds
        config_files = $configFiles
        plugins = $plugins
        snippets = $snippets
        themes = $themes
        templates = $templates
        template_config = $templateConfig
        daily_notes_config = $dailyConfig
    }
    codex = [ordered]@{
        executable_present = [bool]$codexExe
        executable_path_kind = if ($codexExe) {
            if ($codexExe.FullName -like "$env:LOCALAPPDATA\OpenAI\Codex\bin\*") { "Codex Desktop bundled CLI" }
            elseif ($codexExe.FullName -like "*WinGet*") { "WinGet Codex CLI" }
            else { "Other Codex CLI" }
        } else { $null }
        executable_file_version = if ($codexExe) { $codexExe.VersionInfo.FileVersion } else { $null }
        local_skills = $localSkills
        academic_research_suite = if ($arsManifest) {
            [ordered]@{
                present = $true
                adapter_version = $arsManifest.adapter_version
                generated_date = $arsManifest.generated_date
                source_repositories = @($arsManifest.source_repositories | ForEach-Object {
                    [ordered]@{ name = $_.name; url = $_.url; commit = $_.commit }
                })
            }
        } else {
            [ordered]@{ present = $false }
        }
    }
    git = [ordered]@{
        executable_present = $gitAvailable
        repository_present = (Test-Path -LiteralPath (Join-Path $VaultPath ".git") -PathType Container)
        branch = $gitBranch
        head = $gitHead
        remote_host = $gitRemoteHost
    }
}

$json = $report | ConvertTo-Json -Depth 12

$md = New-Object System.Text.StringBuilder
[void]$md.AppendLine("# Obsidian Environment Audit")
[void]$md.AppendLine()
[void]$md.AppendLine("- Generated: $($report.generated_at)")
[void]$md.AppendLine("- Vault: ``$VaultPath``")
[void]$md.AppendLine("- Obsidian: $($report.obsidian.executable_version)")
[void]$md.AppendLine("- Community plugins: $($plugins.Count), enabled $(@($plugins | Where-Object enabled).Count)")
[void]$md.AppendLine("- Core plugins: enabled $($coreEnabled.Count), disabled $($coreDisabled.Count)")
[void]$md.AppendLine("- Templates: $($templates.Count)")
[void]$md.AppendLine("- Vault-local Codex skills: $($localSkills.Count)")
[void]$md.AppendLine("- Academic Research Suite: $(if ($arsManifest) { "v$($arsManifest.adapter_version)" } else { "not detected" })")
[void]$md.AppendLine("- Git: $(if ($report.git.repository_present) { "local repository on $gitBranch" } else { "not initialized" })")
[void]$md.AppendLine()
[void]$md.AppendLine("## Community plugins")
[void]$md.AppendLine()
[void]$md.AppendLine("| ID | Name | Version | Enabled |")
[void]$md.AppendLine("|---|---|---:|:---:|")
foreach ($plugin in $plugins) {
    [void]$md.AppendLine("| $($plugin.id) | $($plugin.name) | $($plugin.version) | $(if ($plugin.enabled) { "yes" } else { "no" }) |")
}
[void]$md.AppendLine()
[void]$md.AppendLine("## Vault-local skills")
[void]$md.AppendLine()
foreach ($skill in $localSkills) {
    [void]$md.AppendLine("- ``$($skill.name)``: $($skill.description)")
}
[void]$md.AppendLine()
[void]$md.AppendLine("## Privacy boundary")
[void]$md.AppendLine()
[void]$md.AppendLine("The audit does not read or output note contents, Claudian sessions, API/MCP tokens, Git credentials, device IDs, full remote URLs, or workspace layout.")

if (-not $NoWrite) {
    New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $jsonPath = Join-Path $OutputDirectory "obsidian-environment-$stamp.json"
    $mdPath = Join-Path $OutputDirectory "obsidian-environment-$stamp.md"
    [System.IO.File]::WriteAllText($jsonPath, $json + [Environment]::NewLine, $Utf8NoBom)
    [System.IO.File]::WriteAllText($mdPath, $md.ToString(), $Utf8NoBom)
    Write-Output "JSON=$jsonPath"
    Write-Output "MARKDOWN=$mdPath"
}
else {
    Write-Output $md.ToString()
}
