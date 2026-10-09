#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -f "$ROOT/frontend/dist/index.html" ]]; then
	echo "Frontend build not found. Run scripts/setup.sh before starting." >&2
	exit 1
fi

PYTHON_BIN="${PYTHON_BIN:-python3}"
if [[ -x "$ROOT/.venv/bin/python" && -z "${RAILWAY_ENVIRONMENT:-}" && -z "${RAILWAY_SERVICE_ID:-}" ]]; then
	PYTHON_BIN="$ROOT/.venv/bin/python"
fi

SETTINGS_JSON="$($PYTHON_BIN - <<'PY'
import json
import sys

from backend.config import get_settings

settings = get_settings()
missing = [
	name
	for name, value in (
		("DATABASE_URL", settings.database_url),
		("OPENAI_API_KEY", settings.openai_api_key),
		("LLM_MODEL", settings.llm_model),
		("EMBEDDING_MODEL", settings.embedding_model),
	)
	if not value
]
if missing:
	print("Missing required settings: " + ", ".join(missing), file=sys.stderr)
	sys.exit(1)
print(json.dumps({"host": settings.backend_host, "port": settings.backend_port}))
PY
)" || exit $?

if [[ ! -f "$ROOT/frontend/dist/index.html" ]]; then
	echo "Frontend build not found. Run scripts/setup.sh during the build phase." >&2
	exit 1
fi

SETTINGS_HOST="$("$PYTHON_BIN" -c 'import json,sys; print(json.load(sys.stdin)["host"])' <<<"$SETTINGS_JSON")"
HOST="${BACKEND_HOST:-$SETTINGS_HOST}"
SETTINGS_PORT="$("$PYTHON_BIN" -c 'import json,sys; print(json.load(sys.stdin)["port"])' <<<"$SETTINGS_JSON")"
PORT="${PORT:-${BACKEND_PORT:-$SETTINGS_PORT}}"
if ! [[ "$PORT" =~ ^[0-9]+$ ]] || ((PORT < 1 || PORT > 65535)); then
	echo "PORT must be an integer between 1 and 65535." >&2
	exit 1
fi

echo "Starting Torilo AI Student Assistant on ${HOST}:${PORT}"
exec "$PYTHON_BIN" -m uvicorn backend.api.main:app --host "$HOST" --port "$PORT"