[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$Repository,

    [string]$Branch = 'main'
)

$ErrorActionPreference = 'Stop'
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)

$gh = (Get-Command gh -ErrorAction SilentlyContinue).Source
$isWindowsPlatform = [Environment]::OSVersion.Platform -eq [PlatformID]::Win32NT
if (-not $gh -and $isWindowsPlatform) {
    $candidate = Join-Path $env:ProgramFiles 'GitHub CLI/gh.exe'
    if (Test-Path -LiteralPath $candidate) {
        $gh = $candidate
    }
}
if (-not $gh) {
    throw 'GitHub CLI (gh) was not found.'
}

if (-not (git rev-parse --is-inside-work-tree 2>$null)) {
    throw 'Run this script inside a Git repository.'
}
if (git status --porcelain) {
    throw 'The working tree must be clean before API publication.'
}
& $gh auth status *> $null
if ($LASTEXITCODE -ne 0) {
    throw 'GitHub CLI is not authenticated.'
}

function Invoke-GhJson {
    param(
        [string]$Endpoint,
        [ValidateSet('POST', 'PUT', 'PATCH')]
        [string]$Method,
        [object]$Payload
    )

    $json = $Payload | ConvertTo-Json -Depth 8 -Compress
    $result = $json | & $gh api --method $Method $Endpoint --input - 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "GitHub API request failed for ${Endpoint}: $($result -join [Environment]::NewLine)"
    }
    return (($result -join [Environment]::NewLine) | ConvertFrom-Json)
}

function Invoke-GhGet {
    param([string]$Endpoint)

    $result = & $gh api $Endpoint 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "GitHub API request failed for ${Endpoint}: $($result -join [Environment]::NewLine)"
    }
    return (($result -join [Environment]::NewLine) | ConvertFrom-Json)
}

function New-CommitPayload {
    param(
        [string]$Tree,
        [string[]]$Parents
    )

    $message = ((git show -s --format='%B' HEAD) -join "`n").TrimEnd()
    return [ordered]@{
        message = $message
        tree = $Tree
        parents = $Parents
        author = [ordered]@{
            name = git show -s --format='%an' HEAD
            email = git show -s --format='%ae' HEAD
            date = git show -s --format='%aI' HEAD
        }
        committer = [ordered]@{
            name = git show -s --format='%cn' HEAD
            email = git show -s --format='%ce' HEAD
            date = git show -s --format='%cI' HEAD
        }
    }
}

function Convert-HeadToApiCanonicalRootCommit {
    # GitHub's Git Data API canonicalizes timestamps to UTC and serializes the
    # submitted message without a final LF. Rebuild the still-unpublished root
    # commit byte-for-byte so its SHA can be verified against the API object.
    $revision = (git rev-list --parents -n 1 HEAD).Trim().Split(' ')
    if ($revision.Count -ne 1) {
        throw 'API fallback is limited to an unpublished root commit.'
    }

    $oldHead = (git rev-parse HEAD).Trim()
    $branchRef = (git symbolic-ref HEAD).Trim()
    $tree = (git rev-parse 'HEAD^{tree}').Trim()
    $message = ((git show -s --format='%B' HEAD) -join "`n").TrimEnd()
    $authorName = git show -s --format='%an' HEAD
    $authorEmail = git show -s --format='%ae' HEAD
    $authorEpoch = git show -s --format='%at' HEAD
    $committerName = git show -s --format='%cn' HEAD
    $committerEmail = git show -s --format='%ce' HEAD
    $committerEpoch = git show -s --format='%ct' HEAD
    $rawCommit = "tree $tree`nauthor $authorName <$authorEmail> $authorEpoch +0000`ncommitter $committerName <$committerEmail> $committerEpoch +0000`n`n$message"
    $commitFile = Join-Path ([IO.Path]::GetTempPath()) ("codex-api-commit-{0}.txt" -f [guid]::NewGuid().ToString('N'))
    try {
        [IO.File]::WriteAllText($commitFile, $rawCommit, [Text.UTF8Encoding]::new($false))
        $newHead = (git hash-object -t commit -w $commitFile).Trim()
        if ($LASTEXITCODE -ne 0) {
            throw 'git hash-object failed.'
        }
        if ($newHead -ne $oldHead) {
            git update-ref $branchRef $newHead $oldHead
            if ($LASTEXITCODE -ne 0) {
                throw 'git update-ref failed.'
            }
        }
    }
    finally {
        if ([IO.File]::Exists($commitFile)) {
            [IO.File]::Delete($commitFile)
        }
    }
}

Convert-HeadToApiCanonicalRootCommit

$repositoryStateJson = & $gh repo view $Repository --json isEmpty 2>&1
if ($LASTEXITCODE -ne 0) {
    throw "Unable to inspect repository state: $($repositoryStateJson -join [Environment]::NewLine)"
}
$repositoryState = ($repositoryStateJson -join [Environment]::NewLine) | ConvertFrom-Json
$bootstrapSha = $null
if ($repositoryState.isEmpty) {
    # GitHub rejects Git Data API tree/ref creation until an empty repository
    # has its first branch. This temporary file disappears from the final tree.
    $bootstrap = Invoke-GhJson -Endpoint "repos/$Repository/contents/.codex-bootstrap" -Method PUT -Payload ([ordered]@{
        message = 'Initialize repository branch'
        content = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes("Temporary bootstrap; removed by the next commit.`n"))
        branch = $Branch
    })
    $bootstrapSha = $bootstrap.commit.sha
}
else {
    # Recover safely from an interrupted earlier publication only when the
    # remote branch contains exactly the temporary bootstrap file.
    $currentRef = Invoke-GhGet -Endpoint "repos/$Repository/git/ref/heads/$Branch"
    $currentCommit = Invoke-GhGet -Endpoint "repos/$Repository/git/commits/$($currentRef.object.sha)"
    $currentTree = Invoke-GhGet -Endpoint "repos/$Repository/git/trees/$($currentCommit.tree.sha)?recursive=1"
    $remoteBlobs = @($currentTree.tree | Where-Object { $_.type -eq 'blob' })
    if ($remoteBlobs.Count -eq 1 -and $remoteBlobs[0].path -eq '.codex-bootstrap') {
        $bootstrapSha = $currentRef.object.sha
    }
    else {
        throw "Remote branch $Branch is not empty; use normal Git transport for updates."
    }
}

$zip = Join-Path ([IO.Path]::GetTempPath()) ("codex-git-archive-{0}.zip" -f [guid]::NewGuid().ToString('N'))
try {
    git archive --format=zip -o $zip HEAD
    if ($LASTEXITCODE -ne 0) {
        throw 'git archive failed.'
    }

    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $archive = [IO.Compression.ZipFile]::OpenRead($zip)
    try {
        $modeMap = @{}
        foreach ($line in (git ls-tree -r HEAD)) {
            if ($line -match '^(\d+) blob [0-9a-f]+\t(.+)$') {
                $modeMap[$Matches[2]] = $Matches[1]
            }
        }

        $strictUtf8 = [System.Text.UTF8Encoding]::new($false, $true)
        $entries = @()
        foreach ($entry in $archive.Entries) {
            if ($entry.FullName.EndsWith('/')) {
                continue
            }

            $stream = $entry.Open()
            $memory = [IO.MemoryStream]::new()
            try {
                $stream.CopyTo($memory)
                # git archive applies checkout EOL rules on Windows. GitHub's
                # tree hash is based on index blobs, whose text is normalized.
                $content = $strictUtf8.GetString($memory.ToArray()).Replace("`r`n", "`n")
            }
            finally {
                $memory.Dispose()
                $stream.Dispose()
            }

            $entries += [ordered]@{
                path = $entry.FullName
                mode = $modeMap[$entry.FullName]
                type = 'blob'
                content = $content
            }
        }
    }
    finally {
        $archive.Dispose()
    }

    $tree = Invoke-GhJson -Endpoint "repos/$Repository/git/trees" -Method POST -Payload ([ordered]@{ tree = $entries })
    $localTree = (git rev-parse 'HEAD^{tree}').Trim()
    if ($tree.sha -ne $localTree) {
        throw "Uploaded tree differs from the local Git tree: remote=$($tree.sha), local=$localTree"
    }

    $rootCommit = Invoke-GhJson -Endpoint "repos/$Repository/git/commits" -Method POST -Payload (New-CommitPayload -Tree $tree.sha -Parents @())
    $localHead = (git rev-parse HEAD).Trim()
    if ($rootCommit.sha -ne $localHead) {
        throw "Uploaded root commit differs from local HEAD: remote=$($rootCommit.sha), local=$localHead"
    }

    if ($bootstrapSha) {
        # Keep the exact local commit as a parent so a later normal Git fetch can
        # fast-forward the local branch to the API-published merge commit.
        $mergeCommit = Invoke-GhJson -Endpoint "repos/$Repository/git/commits" -Method POST -Payload (New-CommitPayload -Tree $tree.sha -Parents @($bootstrapSha, $rootCommit.sha))
        $null = Invoke-GhJson -Endpoint "repos/$Repository/git/refs/heads/$Branch" -Method PATCH -Payload ([ordered]@{
            sha = $mergeCommit.sha
            force = $false
        })
        Write-Host "Published $Repository@$($mergeCommit.sha) through the empty-repository bootstrap path; tree hash verified."
    }
    else {
        $ref = Invoke-GhJson -Endpoint "repos/$Repository/git/refs" -Method POST -Payload ([ordered]@{
            ref = "refs/heads/$Branch"
            sha = $rootCommit.sha
        })
        Write-Host "Published $Repository@$($ref.object.sha); tree hash verified."
    }
}
finally {
    if ([IO.File]::Exists($zip)) {
        [IO.File]::Delete($zip)
    }
}
