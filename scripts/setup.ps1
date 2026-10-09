$ErrorActionPreference = "Stop"
$repositoryRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repositoryRoot
try {
	$python = Join-Path $repositoryRoot ".venv\Scripts\python.exe"
	if (-not (Test-Path $python)) {
		python -m venv (Join-Path $repositoryRoot ".venv")
		if ($LASTEXITCODE -ne 0) { throw "Could not create the Python virtual environment." }
	}
	& $python -m pip install --disable-pip-version-check -r requirements-dev.txt
	if ($LASTEXITCODE -ne 0) { throw "Backend dependency installation failed." }
	npm ci --prefix frontend
	if ($LASTEXITCODE -ne 0) { throw "Frontend dependency installation failed." }
	npm --prefix frontend run build
	if ($LASTEXITCODE -ne 0) { throw "Frontend production build failed." }
	Write-Host "Setup complete. Run scripts/start.ps1 to launch the application."
}
finally {
	Pop-Location
}