param([switch]$SkipTests, [switch]$BundleBin)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not $SkipTests) {
    python -X utf8 -m unittest discover -s tests -v
    if ($LASTEXITCODE -ne 0) { throw 'Tests failed.' }
}
$taskVersion = python -X utf8 -c "from dm_migration import __version__; print(__version__)"
if ($LASTEXITCODE -ne 0) { throw 'Could not read application version.' }
$taskExeName = "DM-Migration-$taskVersion"
$taskExtraData = @()
if ($BundleBin) {
    foreach ($taskToolName in @('dexp.exe', 'dimp.exe', 'dodbc.dll')) {
        if (-not (Test-Path -LiteralPath (Join-Path $PSScriptRoot "bin\$taskToolName") -PathType Leaf)) {
            throw "Bundled build requires bin\$taskToolName and its official dependencies."
        }
    }
    $taskExeName += '-standalone'
    $taskExtraData = @('--add-data', 'bin;bin')
}
python -X utf8 -m PyInstaller --noconfirm --onefile --windowed --name $taskExeName --icon assets/dm.ico --add-data 'web;web' @taskExtraData --hidden-import tkinter --hidden-import tkinter.filedialog app.py
if ($LASTEXITCODE -ne 0) { throw 'Build failed. Install PyInstaller with: python -m pip install pyinstaller' }
Copy-Item -LiteralPath (Join-Path $PSScriptRoot "dist\$taskExeName.exe") -Destination (Join-Path $PSScriptRoot "$taskExeName.exe") -Force
if ($BundleBin) {
    Write-Output "Built $taskExeName.exe with the official bin folder embedded."
} else {
    Write-Output "Built $taskExeName.exe. Keep the bin folder beside the executable."
}
