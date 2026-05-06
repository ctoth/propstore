param(
    [string[]]$Roots = @(),
    [switch]$Force,
    [switch]$WhatIf,
    [int]$Density = 150,
    [int]$Quality = 90,
    [int]$MaxDimension = 1960
)

$ErrorActionPreference = "Stop"

function Resolve-RepoRoot {
    $scriptDir = Split-Path -Parent $PSCommandPath
    return (Resolve-Path (Join-Path $scriptDir "..")).Path
}

function Default-PaperRoots {
    $repoRoot = Resolve-RepoRoot
    $codeRoot = Split-Path -Parent $repoRoot
    $roots = @()
    foreach ($dir in Get-ChildItem -LiteralPath $codeRoot -Directory) {
        $papers = Join-Path $dir.FullName "papers"
        if (Test-Path -LiteralPath $papers -PathType Container) {
            $roots += $papers
        }
    }
    return $roots | Sort-Object -Unique
}

function Resolve-PaperRoots {
    param([string[]]$InputRoots)

    if ($InputRoots.Count -eq 0) {
        return Default-PaperRoots
    }

    $resolved = @()
    foreach ($root in $InputRoots) {
        $path = (Resolve-Path -LiteralPath $root).Path
        if ((Split-Path -Leaf $path) -eq "papers") {
            $resolved += $path
            continue
        }
        $papers = Join-Path $path "papers"
        if (Test-Path -LiteralPath $papers -PathType Container) {
            $resolved += (Resolve-Path -LiteralPath $papers).Path
            continue
        }
        throw "Root has no papers directory: $root"
    }
    return $resolved | Sort-Object -Unique
}

function PdfInfo-Command {
    $cmd = Get-Command pdfinfo -ErrorAction SilentlyContinue
    if ($null -eq $cmd) {
        return $null
    }
    return $cmd.Source
}

function Get-PdfPageCount {
    param(
        [string]$PdfPath,
        [string]$PdfInfo
    )

    if ([string]::IsNullOrWhiteSpace($PdfInfo)) {
        return $null
    }
    try {
        $output = & $PdfInfo $PdfPath 2>&1
    } catch {
        return $null
    }
    if ($LASTEXITCODE -ne 0) {
        return $null
    }
    foreach ($line in $output) {
        if ($line -match "^Pages:\s+(\d+)\s*$") {
            return [int]$Matches[1]
        }
    }
    return $null
}

function Find-PaperPdf {
    param([string]$PaperDir)

    $preferred = Join-Path $PaperDir "paper.pdf"
    if (Test-Path -LiteralPath $preferred -PathType Leaf) {
        return $preferred
    }
    $pdfs = Get-ChildItem -LiteralPath $PaperDir -File -Filter "*.pdf" |
        Sort-Object Name
    if ($pdfs.Count -gt 0) {
        return $pdfs[0].FullName
    }
    return $null
}

function Existing-PageImages {
    param([string]$PngDir)

    if (-not (Test-Path -LiteralPath $PngDir -PathType Container)) {
        return @()
    }
    return @(Get-ChildItem -LiteralPath $PngDir -File -Filter "page-*.png")
}

function Should-Convert {
    param(
        [string]$PngDir,
        [Nullable[int]]$PageCount,
        [bool]$Force
    )

    if ($Force) {
        return $true
    }

    $existing = Existing-PageImages $PngDir
    if ($existing.Count -eq 0) {
        return $true
    }

    if ($null -eq $PageCount) {
        return $false
    }

    return $existing.Count -lt $PageCount
}

$magick = (Get-Command magick -ErrorAction SilentlyContinue)
if ($null -eq $magick) {
    throw "ImageMagick 'magick' command was not found on PATH"
}
$pdfInfo = PdfInfo-Command

$paperRoots = Resolve-PaperRoots $Roots
$converted = 0
$skipped = 0
$failed = 0

Write-Host "Using magick: $($magick.Source)"
if ($null -eq $pdfInfo) {
    Write-Host "pdfinfo not available; existing non-empty pngs directories will be treated as complete."
} else {
    Write-Host "Using pdfinfo: $pdfInfo"
}
Write-Host "Paper roots:"
foreach ($root in $paperRoots) {
    Write-Host "  $root"
}

foreach ($papersRoot in $paperRoots) {
    $paperDirs = Get-ChildItem -LiteralPath $papersRoot -Directory |
        Where-Object { $_.Name -ne "tagged" } |
        Sort-Object FullName

    foreach ($paperDir in $paperDirs) {
        $pdf = Find-PaperPdf $paperDir.FullName
        if ($null -eq $pdf) {
            $skipped += 1
            Write-Host "SKIP no-pdf $($paperDir.FullName)"
            continue
        }

        $pngDir = Join-Path $paperDir.FullName "pngs"
        $pageCount = Get-PdfPageCount -PdfPath $pdf -PdfInfo $pdfInfo
        if (-not (Should-Convert -PngDir $pngDir -PageCount $pageCount -Force $Force.IsPresent)) {
            $skipped += 1
            $existingCount = (Existing-PageImages $pngDir).Count
            $expected = if ($null -eq $pageCount) { "unknown" } else { [string]$pageCount }
            Write-Host "SKIP complete $($paperDir.FullName) existing=$existingCount expected=$expected"
            continue
        }

        $expectedText = if ($null -eq $pageCount) { "unknown" } else { [string]$pageCount }
        Write-Host "CONVERT $pdf expected_pages=$expectedText"
        if ($WhatIf) {
            $converted += 1
            continue
        }

        try {
            New-Item -ItemType Directory -Force -Path $pngDir | Out-Null
            $outPattern = Join-Path $pngDir "page-%03d.png"
            & $magick.Source -density $Density $pdf -quality $Quality -resize "$($MaxDimension)x$($MaxDimension)>" $outPattern
            if ($LASTEXITCODE -ne 0) {
                throw "magick exited with code $LASTEXITCODE"
            }
            $converted += 1
        } catch {
            $failed += 1
            Write-Host "FAIL $pdf :: $($_.Exception.Message)"
        }
    }
}

Write-Host "SUMMARY converted=$converted skipped=$skipped failed=$failed"
if ($failed -gt 0) {
    exit 1
}
