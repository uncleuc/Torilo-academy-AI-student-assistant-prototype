# Contributing

## Before Editing

1. Confirm the current branch and inspect `git status`; preserve existing changes you did not make.
2. Work within the owning group's files or coordinate cross-group contract changes first.
3. Never commit `.env`, API keys, real student data, Chroma databases, virtual environments, or build outputs.
4. Keep public interfaces stable unless a contract change is intentional and covered by tests/documentation.

## Branches and Pull Requests

Use a focused feature branch based on the team's agreed integration branch. Open a pull request to the agreed target; do not push directly to protected `develop` or `main`. Review the diff and ownership before staging. Avoid force-pushing shared branches.

```powershell
git status --short --branch
git diff --check
git diff
```

Stage only the intended files, use a descriptive commit message, and include test output and any deployment/configuration prerequisites in the pull request.

## Validation

From the repository root:

```powershell
python -m pytest -q
python -m ruff check backend tests
python -m compileall -q backend scripts
```

For the frontend:

```powershell
Set-Location frontend
npm test
npm run build
```

See [testing.md](testing.md) for suite scope and real-service checks. Tests should use fake models/retrievers and isolated databases unless explicitly marked as integration tests.

## Data and Security Rules

- Knowledge-base facts are answerable only when the file is in `knowledge_base/index.json` with `approved: true`.
- All database seed data is synthetic and uses reserved `.invalid` email addresses.
- Conversation IDs are not authentication tokens; do not use them to authorize student-record access.
- Do not log prompts, user contents, API keys, database URLs, student data, or raw exception details.
- Do not weaken unknown, approval, injection, or privacy tests to make a change pass.

## Ownership Coordination

Coordinate shared changes to `requirements*.txt`, `pyproject.toml`, scenario JSON, API contracts, and deployment files with the integration/test owners. Update relevant docs in the same change when runtime commands, environment variables, interfaces, or ownership boundaries change.