# Frontend

## Development

The UI uses React 19 and Vite. From the repository root:

```powershell
Set-Location frontend
npm ci
npm run dev
```

Vite serves the app on port 5173. It proxies `/api/*` to `API_PROXY_TARGET` (default `http://127.0.0.1:8000`) so the browser uses a same-origin URL. `VITE_ALLOWED_HOSTS` is a comma-separated list of hostnames accepted by Vite; do not set it to `true` or a wildcard.

## Production

Run `npm run build` to create `frontend/dist`. The integrated FastAPI app serves those files from `/` while retaining the `/api/*` routes. On Railway, one public service/domain handles both UI and API; FastAPI binds to the platform-provided `PORT`.

`VITE_API_URL` is optional. Leave it blank for same-origin `/api` requests. If set, it must be a public API origin, not a secret. Never put `DATABASE_URL`, `OPENAI_API_KEY`, or vector credentials into browser code.

## Chat Contract

The frontend sends `{ "message": "...", "conversation_id": "..." }` to `POST /api/chat`. It omits the ID for a new conversation, then reuses the server-returned `conversation_id`. It validates `answer`, `sources`, and ID before rendering.

The UI does not generate assistant text. Failed requests preserve the user question, show a retryable error and do not add an assistant answer. Source cards display only whitelisted citation fields. The conversation ID alone is stored in tab `sessionStorage`; transcript contents are not persisted there.

## Tests

```powershell
Set-Location frontend
npm test
npm run build
```

`src/pages/Chat.test.jsx` covers backend response/source display, conversation-ID reuse, and error/retry behavior. HTTP is mocked at the client boundary in tests; production requests still go to FastAPI.