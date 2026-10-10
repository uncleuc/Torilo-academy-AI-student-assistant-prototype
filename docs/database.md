# Database

## Runtime Connection

The application uses PostgreSQL and synchronous SQLAlchemy 2.x sessions. Set `DATABASE_URL` in the process environment or repository-root `.env`; credentials are never hard-coded. The engine is created during FastAPI lifespan startup and disposed at shutdown. PostgreSQL URL forms `postgres://` and `postgresql://` are normalized to the `psycopg` SQLAlchemy driver.

Do not put a real database URL in frontend `VITE_*` variables. Those variables are shipped to browsers.

## Tables

| Table | Role |
| --- | --- |
| `instructors` | Public instructor name/active state; associated with courses and classes. |
| `courses` | Public course name, description, level, duration, active state, optional instructor. |
| `classes` | Scheduled occurrence with course, optional instructor, times, location and status. |
| `students` | Private student identity fields. No unauthenticated assistant tool returns these records. |
| `enrollments` | Student/course association, optional class, status and enrollment timestamp. |

Constraints include unique instructor/student email, positive course duration when specified, valid class/enrollment status, `ends_at > starts_at`, and one enrollment per student/course. Foreign keys and query indexes are defined in `backend/database/models.py` and `backend/database/schema.sql`.

## Tools

`build_database_tools(session_factory)` returns the fixed read-only allowlist:

| Tool | Behavior |
| --- | --- |
| `get_available_courses()` | Active courses ordered by name and ID. |
| `get_course_details(course_id)` | Active course details or `None`. |
| `get_course_instructor(course_id)` | Active course/instructor association or `None`. |
| `get_active_classes()` | Explicitly active classes whose course is active. |
| `search_classes(course_name)` | Matching active/upcoming classes with schedule, location, instructor, and demo/live provenance. |
| `search_courses(query)` | Bounded case-insensitive substring search on active course names, max 20 results. |

All result records are plain dictionaries with string `course_id` values. Tools use short-lived sessions and omit student personal information. A course-name question resolves an ID only after a unique search result.

Instructor questions search approved RAG evidence first and fall back to the course/instructor tools only when no approved instructor assignment is found. Class schedules are dynamic and use `search_classes` directly, matching the normalized course name and returning planned/upcoming or active records.

The application exposes database tools when `DATABASE_DATA_VERIFIED=true`, or in development only when `DATABASE_DEMO_MODE=true`. Leave verified false for synthetic fixtures. Demo results carry `data_status=synthetic_demo` and must be described as sample data, never as actual Academy staff or schedules. Demo mode is ignored outside development. With both modes disabled, database-backed chat requests receive a support handoff and the public course API returns 503. Setting verified true is an operator assertion; it does not itself verify, sanitize, or refresh records. Private student records remain unavailable because no authenticated student-specific tools are implemented.

## Schema and Seed Lifecycle

`backend/database/schema.sql` is the PostgreSQL reference schema. Railway's `scripts/initialize_database.py` bootstrap applies it only when none of the five app tables exist, does nothing when all are present, and refuses a partial schema. Existing deployments must apply reviewed files under `backend/database/migrations/`; `001_course_duration_nullable.sql` permits null when the approved KB does not establish a single duration. Do not use `Base.metadata.create_all()` in production.

`python -m backend.database.seed` is for local/test databases only. It creates ORM tables and merges deterministic demo fixtures: the active course names mirror the KB catalog, while instructor identities and four added class schedules are invented test records clearly marked as demo. Never run it against production. The two removed student/enrollment seed files are optional and are not recreated; existing database rows remain untouched.

## Tests

`tests/test_group3_contracts.py` uses isolated SQLite/`StaticPool` to verify seed idempotency, tools, chat delegation, request validation, health, and both the default-off and explicitly verified course endpoints. PostgreSQL-specific schema/production migrations require a separately isolated PostgreSQL test database.
