# API

FastAPI is the public application boundary. In local development it listens on `http://localhost:8000`; the frontend is normally `http://localhost:5173` and proxies `/api` to it. In production, the built frontend and API can share one origin.

Interactive OpenAPI documentation is available at `/docs`; the schema is `/openapi.json`.

## `POST /api/chat`

Request:

```json
{
	"message": "What is the attendance policy?",
	"conversation_id": "optional-existing-id"
}
```

`message` is trimmed, required, and limited to 8,000 characters. `conversation_id` is optional, trimmed, and limited to 128 characters. Extra request properties are rejected.

Response:

```json
{
	"answer": "Answer generated from the current approved evidence.",
	"sources": [
		{
			"document": "policies/attendance_and_participation.md",
			"title": "Torilo Academy — Attendance and Participation Policy",
			"source_type": "attendance_and_participation_policy"
		}
	],
	"conversation_id": "server-or-client-conversation-id"
}
```

The route calls the injected `run_student_assistant(message, conversation_id)` exactly once and validates the returned mapping. It does not invent a replacement answer. Source fields are citation metadata; the API does not return retrieved chunk text as source cards.

## Other Endpoints

| Method/path | Purpose |
| --- | --- |
| `GET /api/health` | Readiness check; executes `SELECT 1` against PostgreSQL and returns `{"status":"healthy","database":"healthy"}`. |
| `GET /api/courses` | Returns active course records when verified DB access is enabled, or in development demo mode; otherwise 503. Each row includes `data_status`. |
| `GET /api/courses/{course_id}` | Returns an active course or 404 when verified DB access or development demo mode is enabled; otherwise 503. |

## Status Codes

| Status | Meaning |
| --- | --- |
| 200 | Successful chat, health, or course request. |
| 404 | Requested active course is not present. |
| 422 | Invalid request or assistant input validation failure. |
| 502 | Assistant/tool returned malformed data. |
| 503 | Assistant or required data service unavailable. |
| 500 | Unexpected internal failure; response omits internal details. |

Validation, database, and unexpected error handlers return safe messages. Never expose credentials, SQL, prompts, stack traces, or private student records in a response.

## CORS and Same-Origin Routing

FastAPI reads the comma-separated `FRONTEND_URL` setting as its CORS allowlist. CORS is not needed for the normal Vite flow because the browser calls a relative `/api` path and Vite proxies it to FastAPI. Do not use `allow_origins=["*"]` as a substitute for configuring deployment origins.
`DATABASE_DATA_VERIFIED` defaults to false. `DATABASE_DEMO_MODE=true` exposes clearly marked seed records only when `ENVIRONMENT=development`; those responses contain `data_status=synthetic_demo` and must not be described as real Academy staff or current classes. Set `DATABASE_DATA_VERIFIED=true` only after loading and reviewing current authorized Academy records. It is an operator assertion, not automatic data-quality validation.

## Local API Check

```powershell
Invoke-RestMethod http://localhost:8000/api/health
Invoke-RestMethod http://localhost:8000/api/courses
```

Start the backend with `scripts/start.ps1` on Windows or `bash scripts/start.sh` on Linux/WSL. The production launcher honors Railway's injected `PORT`.
