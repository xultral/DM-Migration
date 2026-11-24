param([switch]$SkipBuild, [switch]$Standalone)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not $SkipBuild) {
    & (Join-Path $PSScriptRoot 'build.ps1')
    if ($LASTEXITCODE -ne 0) { throw 'Application build failed.' }
    if ($Standalone) {
        & (Join-Path $PSScriptRoot 'build.ps1') -SkipTests -BundleBin
        if ($LASTEXITCODE -ne 0) { throw 'Standalone build failed.' }
    }
}
$taskPackageArguments = @('-X', 'utf8', 'scripts/package_release.py')
if ($Standalone) { $taskPackageArguments += '--standalone' }
python @taskPackageArguments
if ($LASTEXITCODE -ne 0) { throw 'Release packaging failed.' }
