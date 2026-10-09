# Troubleshooting

## App fails during startup

- Check `DATABASE_URL`, `OPENAI_API_KEY`, `LLM_MODEL` and `EMBEDDING_MODEL` exist in the process environment. Do not paste their values into logs or issue reports.
- Confirm PostgreSQL is reachable and the five schema tables exist. The Railway pre-deploy bootstrap only initializes a completely empty database; it refuses partial schemas.
- Confirm the Railway `PORT` is passed through. `scripts/start.sh` binds to `0.0.0.0` and prioritizes `$PORT`.
- The app embeds approved documents during startup. A missing/invalid registry entry or unavailable embedding API prevents initialization; check the approved index and provider availability.

## Chat says it lacks verified information

1. Check the question's route with the regression tests in `tests/test_question_routing.py` and `tests/test_roadmap_scenarios.py`.
2. Confirm the expected file exists in `knowledge_base/index.json` with `approved: true`.
3. Confirm `CHROMA_PERSIST_DIRECTORY` points to the volume that contains the configured model-specific collection. A missing or ephemeral volume can result in an empty index.
4. Verify retrieved results include `approved: true` metadata and non-empty text. Group 2 will return the fixed unknown answer if no usable evidence is supplied.
5. Do not lower the evidence gate just to force an answer. Fix intent mapping, registry metadata or indexing instead.

## Database answers are missing

- `GET /api/health` checks PostgreSQL connectivity.
- Run `python -m scripts.initialize_database` only for an empty development/production database as part of the reviewed first-deploy process. It does nothing for a complete schema and refuses a partial schema.
- `python -m backend.database.seed` loads synthetic local fixtures and must not be run in production.
- Course tools return active courses only. Instructor/detail requests require one unique course search match.

## Browser cannot reach API

- In local Vite development, the browser calls relative `/api`; Vite proxies to `API_PROXY_TARGET` (default `http://127.0.0.1:8000`).
- Confirm the Vite and FastAPI processes are listening and inspect `/api/health` through the frontend origin.
- If calling the API directly from another origin, include that exact scheme/host/port in comma-separated `FRONTEND_URL`. Same-origin proxy requests do not need CORS.
- Vite rejects unlisted host headers. Add only the exact trusted hostnames to `VITE_ALLOWED_HOSTS`; do not use wildcard host acceptance.
- `torilo.net` requires DNS and a TLS-capable custom-domain ingress. Adding it to a host/CORS allowlist alone does not point it to this machine.

## Railway deployment failures

- Confirm Railpack has Node available through `railpack.json` and the build log shows `npm ci` plus `npm run build` completing.
- Confirm `frontend/dist/index.html` exists in the deployment artifact.
- Attach a Railway volume at `/app/chroma_db` and set `CHROMA_PERSIST_DIRECTORY` to that mount path.
- Check Railway Postgres variables are referenced in the app service and that the service can connect to its database.
- The service needs public variables for `LLM_MODEL` and `EMBEDDING_MODEL`, and secret variables for `OPENAI_API_KEY` and `DATABASE_URL`.
- Use `/api/health` as the Railway health check. A passing health check verifies PostgreSQL only; it does not test the LLM or retrieval.

## Port already in use

Set `BACKEND_PORT` for local startup or pass Railway's `PORT`. For Vite, set `FRONTEND_PORT`. Both scripts/configs use strict ports rather than silently binding another port.