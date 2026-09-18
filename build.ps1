<#
    Build Cereal Pager into dist\CerealPager.vlt

        .\build.ps1             regenerate art, sync, validate, render, package
        .\build.ps1 -Quick      package only (assets must already exist)

    A .vlt is an ordinary archive whose root holds theme.xml.  VLC has read
    zip-based skins since 0.8.5, and Compress-Archive is built into
    PowerShell 5.1, so that is what this uses.  build.sh produces a tar.gz
    instead; VLC accepts either.

    Needs Python 3 with Pillow on PATH:  pip install pillow
#>
[CmdletBinding()]
param([switch]$Quick)

$ErrorActionPreference = 'Stop'
Set-Location -Path $PSScriptRoot

$name = 'CerealPager'
$out  = Join-Path $PSScriptRoot "dist\$name.vlt"
$zip  = Join-Path $PSScriptRoot "dist\$name.zip"

function Invoke-Step {
    param([string]$Label, [string[]]$Arguments)
    Write-Host "==> $Label" -ForegroundColor Yellow
    & python @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Label failed (exit $LASTEXITCODE)" }
}

if (-not $Quick) {
    Invoke-Step 'artwork'              @('tools/generate_assets.py')
    Invoke-Step 'bitmap declarations'  @('tools/sync_bitmaps.py')
    Invoke-Step 'previews'             @('tools/preview.py')
}
Invoke-Step 'validating theme.xml'     @('tools/validate_theme.py')

Write-Host '==> packaging' -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path (Join-Path $PSScriptRoot 'dist') | Out-Null
Remove-Item -Force -ErrorAction SilentlyContinue $out, $zip

Compress-Archive -Path 'theme.xml', 'assets', 'fonts' -DestinationPath $zip -CompressionLevel Optimal
Rename-Item -Path $zip -NewName "$name.vlt"

$size = '{0:N0} KB' -f ((Get-Item $out).Length / 1KB)
Write-Host "built $out  ($size)" -ForegroundColor Green
Write-Host ''
Write-Host "Install: VLC > Tools > Preferences > Interface > Use custom skin > $out"
