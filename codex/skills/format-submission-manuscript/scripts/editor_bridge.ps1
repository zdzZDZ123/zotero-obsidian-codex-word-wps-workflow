[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$InputDocx,
    [Parameter(Mandatory = $true)][string]$OutputDocx,
    [Parameter(Mandatory = $true)][string]$OutputPdf,
    [ValidateSet('word', 'wps')][string]$Editor,
    [switch]$Visible
)

$ErrorActionPreference = 'Stop'
$app = $null
$document = $null
$started = Get-Date

function Get-ComServer([string]$ProgId) {
    $clsidPath = "Registry::HKEY_CLASSES_ROOT\$ProgId\CLSID"
    if (-not (Test-Path -LiteralPath $clsidPath)) { return $null }
    $clsid = (Get-ItemProperty -LiteralPath $clsidPath).'(default)'
    if (-not $clsid) { return $null }
    $serverPath = "Registry::HKEY_CLASSES_ROOT\CLSID\$clsid\LocalServer32"
    if (-not (Test-Path -LiteralPath $serverPath)) { return $null }
    return (Get-ItemProperty -LiteralPath $serverPath).'(default)'
}

try {
    $input = (Resolve-Path -LiteralPath $InputDocx).Path
    $outputDocxFull = [System.IO.Path]::GetFullPath($OutputDocx)
    $outputPdfFull = [System.IO.Path]::GetFullPath($OutputPdf)
    [System.IO.Directory]::CreateDirectory([System.IO.Path]::GetDirectoryName($outputDocxFull)) | Out-Null
    [System.IO.Directory]::CreateDirectory([System.IO.Path]::GetDirectoryName($outputPdfFull)) | Out-Null
    Copy-Item -LiteralPath $input -Destination $outputDocxFull -Force

    $progId = if ($Editor -eq 'word') { 'Word.Application' } else { 'KWPS.Application' }
    $server = Get-ComServer $progId
    if (-not $server) { throw "$progId is not registered" }
    if ($Editor -eq 'word' -and $server -notmatch '(?i)WINWORD\.EXE') {
        throw "Word.Application is not served by genuine Microsoft Word: $server"
    }
    if ($Editor -eq 'wps' -and $server -notmatch '(?i)wps\.exe') {
        throw "KWPS.Application is not served by WPS Writer: $server"
    }

    $app = New-Object -ComObject $progId
    $app.Visible = [bool]$Visible
    try { $app.DisplayAlerts = 0 } catch { }
    $document = $app.Documents.Open($outputDocxFull)

    $updatedFields = 0
    try { $updatedFields += [int]$document.Fields.Update() } catch { }
    try {
        foreach ($toc in @($document.TablesOfContents)) {
            $toc.Update()
            $updatedFields += 1
        }
    } catch { }
    try {
        foreach ($story in @($document.StoryRanges)) {
            $range = $story
            while ($null -ne $range) {
                try { $updatedFields += [int]$range.Fields.Update() } catch { }
                try { $range = $range.NextStoryRange } catch { $range = $null }
            }
        }
    } catch { }

    $document.Save()
    $pdfExported = $false
    try {
        $document.ExportAsFixedFormat($outputPdfFull, 17)
        $pdfExported = Test-Path -LiteralPath $outputPdfFull -PathType Leaf
    }
    catch {
        try {
            $document.SaveAs2($outputPdfFull, 17)
            $pdfExported = Test-Path -LiteralPath $outputPdfFull -PathType Leaf
        }
        catch {
            $pdfExported = $false
        }
    }
    $document.Close($false)
    $document = $null
    $document = $app.Documents.Open($outputDocxFull)
    $reopenedParagraphs = [int]$document.Paragraphs.Count
    $reopenedTables = [int]$document.Tables.Count
    $document.Close($false)
    $document = $null
    $app.Quit()
    $app = $null

    if (-not (Test-Path -LiteralPath $outputDocxFull -PathType Leaf)) {
        throw 'Editor did not preserve the reviewed DOCX copy.'
    }
    if (-not $pdfExported) {
        throw 'Editor did not export a PDF.'
    }

    [ordered]@{
        status = 'passed'
        editor = $Editor
        prog_id = $progId
        com_server = $server
        output_docx = $outputDocxFull
        output_pdf = $outputPdfFull
        updated_fields = $updatedFields
        reopened = $true
        reopened_paragraphs = $reopenedParagraphs
        reopened_tables = $reopenedTables
        visible = [bool]$Visible
        elapsed_seconds = [Math]::Round(((Get-Date) - $started).TotalSeconds, 3)
    } | ConvertTo-Json -Compress
    exit 0
}
catch {
    [ordered]@{
        status = 'failed'
        editor = $Editor
        error = $_.Exception.Message
        elapsed_seconds = [Math]::Round(((Get-Date) - $started).TotalSeconds, 3)
    } | ConvertTo-Json -Compress
    exit 2
}
finally {
    if ($null -ne $document) {
        try { $document.Close($false) } catch { }
    }
    if ($null -ne $app) {
        try { $app.Quit() } catch { }
    }
    if ($null -ne $document) { [System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($document) | Out-Null }
    if ($null -ne $app) { [System.Runtime.InteropServices.Marshal]::FinalReleaseComObject($app) | Out-Null }
    [GC]::Collect()
    [GC]::WaitForPendingFinalizers()
}
