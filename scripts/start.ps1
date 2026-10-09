$ErrorActionPreference = "Stop"
$repositoryRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repositoryRoot
try {
	$venvPython = Join-Path $repositoryRoot ".venv\Scripts\python.exe"
	$python = if (Test-Path $venvPython) { $venvPython } else { "python" }
	$settingsJson = & $python -c "import json; from backend.config import get_settings; s=get_settings(); print(json.dumps({'host': s.backend_host, 'port': s.backend_port}))"
	if ($LASTEXITCODE -ne 0) {
		throw "Could not load backend settings. Check Python dependencies and .env."
	}
	$server = $settingsJson | ConvertFrom-Json
	if (-not (Test-Path (Join-Path $repositoryRoot "frontend\dist\index.html"))) {
		throw "Frontend build not found. Run scripts/setup.ps1 before starting."
	}
	$port = if ($env:PORT) { [int]$env:PORT } else { [int]$server.port }
	& $python -m uvicorn backend.api.main:app --host $server.host --port $port @args
	exit $LASTEXITCODE
}
finally {
	Pop-Location
}