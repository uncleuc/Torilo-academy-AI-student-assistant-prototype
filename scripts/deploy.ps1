$ErrorActionPreference = "Stop"
$setupScript = Join-Path $PSScriptRoot "setup.ps1"
$startScript = Join-Path $PSScriptRoot "start.ps1"
& $setupScript
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $startScript
exit $LASTEXITCODE