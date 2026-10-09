# Production Deployment

The production topology is one public web service:

```text
Browser -> Railway domain -> FastAPI
							├── /api/* -> API routes
							└── /*     -> built React app
```

FastAPI serves `frontend/dist` when that build exists. The browser uses a relative `/api` URL, so UI and API share the same public origin. PostgreSQL is a separate Railway service; ChromaDB is local persistent storage mounted as a Railway volume.

## Railway setup

1. Create a Railway project and add a PostgreSQL service. Do not use the synthetic fixture database for real student data.
2. Create one app service from this repository. Railpack reads [railpack.json](../railpack.json) to install Node.js for the nested Vite build; Python is detected from `requirements.txt`.
3. Set the app service **Build Command** to `bash scripts/setup.sh` and **Start Command** to `bash scripts/start.sh`. `railway.json` also runs `python -m scripts.initialize_database` as a guarded pre-deploy bootstrap. Railway runs these in separate build and runtime phases.
4. Add a Railway volume mounted at `/app/chroma_db`. Set `CHROMA_PERSIST_DIRECTORY=/app/chroma_db` so embeddings survive redeploys.
5. Set the environment variables below in Railway. Store secrets only in Railway's variable settings, never in the repository.
6. Set the service health check path to `/api/health` and deploy.

Required Railway variables:

```env
DATABASE_URL=${{Postgres.DATABASE_URL}}
OPENAI_API_KEY=<set as a secret in Railway>
LLM_MODEL=<approved chat model>
EMBEDDING_MODEL=text-embedding-3-small
ENVIRONMENT=production
LOG_LEVEL=INFO
BACKEND_HOST=0.0.0.0
CHROMA_PERSIST_DIRECTORY=/app/chroma_db
CHROMA_COLLECTION_NAME=torilo_knowledge_base
FRONTEND_URL=https://<your-railway-domain>,https://ai.softshell-diminished.ts.net,https://torilo.net,https://www.torilo.net
```

`PORT` is supplied by Railway and consumed by `scripts/start.sh`. Do not set it to a fixed port in production. The FastAPI CORS allowlist is only needed for direct cross-origin API use; same-origin `/api` requests through the built frontend do not require browser CORS.

### Custom domain and Tailscale

The Railway-generated domain is the simplest production URL. Attach `torilo.net` or `www.torilo.net` to the Railway service using Railway's custom-domain instructions and configure the requested DNS records there.

Tailscale Funnel only provides `*.ts.net` hostnames. The existing `https://ai.softshell-diminished.ts.net` Funnel can point to the Vite development server for testing, but it is not a production static-server substitute. For a custom domain without Docker/Nginx, use Railway's custom-domain service or a host-installed reverse proxy/tunnel that terminates TLS and forwards to the app.

## One-command local setup and startup

On Linux/macOS/WSL, from the repository root:

```sh
bash scripts/deploy.sh
```

This creates/uses `.venv`, installs backend and frontend dependencies, builds the React app, then starts FastAPI on `BACKEND_HOST` and `PORT` (or `BACKEND_PORT`). Provide a local `.env` with valid `DATABASE_URL`, `OPENAI_API_KEY`, `LLM_MODEL`, and `EMBEDDING_MODEL`. It does not create a database, apply a schema, seed production data, or run database migrations.

On Windows PowerShell, use two commands because the server must remain attached to the terminal:

```powershell
./scripts/setup.ps1
./scripts/start.ps1
```

## Database and knowledge-base lifecycle

The pre-deploy bootstrap applies `backend/database/schema.sql` only when none of the five application tables exist. It no-ops when all five exist and refuses to touch a partial schema. It is not a migration system: review and apply future schema changes explicitly. Do not call `Base.metadata.create_all()` or seed synthetic records in Railway production. The app indexes explicitly approved knowledge-base documents into Chroma during startup and reuses the persistent indexed data when its fingerprint is current. Keep the Chroma volume attached to preserve that index across deployments.

For test execution, run `bash scripts/run_tests.sh` locally; tests use injected/fake services or isolated SQLite and do not require production credentials.