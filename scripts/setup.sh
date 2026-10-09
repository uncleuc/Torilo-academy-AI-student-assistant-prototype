#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ -n "${RAILWAY_ENVIRONMENT:-}" || -n "${RAILWAY_SERVICE_ID:-}" ]]; then
	PYTHON_BIN="${PYTHON_BIN:-python}"
elif [[ -x "$ROOT/.venv/bin/python" ]]; then
	PYTHON_BIN="$ROOT/.venv/bin/python"
else
	PYTHON_BIN="${PYTHON_BIN:-python3}"
	if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
		echo "Python 3 is required to set up this project." >&2
		exit 1
	fi
	"$PYTHON_BIN" -m venv "$ROOT/.venv"
	PYTHON_BIN="$ROOT/.venv/bin/python"
fi

if ! command -v npm >/dev/null 2>&1; then
	echo "Node.js and npm are required to build the frontend." >&2
	exit 1
fi

echo "Installing backend runtime dependencies..."
"$PYTHON_BIN" -m pip install --disable-pip-version-check -r requirements.txt

echo "Installing frontend dependencies and building the production UI..."
npm --prefix frontend ci
npm --prefix frontend run build

echo "Setup complete. Run scripts/start.sh to launch the application."