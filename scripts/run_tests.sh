#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHON_BIN="${PYTHON_BIN:-python3}"
if [[ -x "$ROOT/.venv/bin/python" ]]; then
	PYTHON_BIN="$ROOT/.venv/bin/python"
fi

"$PYTHON_BIN" -m pytest -q