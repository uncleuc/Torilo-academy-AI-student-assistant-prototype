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

Constraints include unique instructor/student email, positive course duration, valid class/enrollment status, `ends_at > starts_at`, and one enrollment per student/course. Foreign keys and query indexes are defined in `backend/database/models.py` and `backend/database/schema.sql`.

## Tools

`build_database_tools(session_factory)` returns the fixed read-only allowlist:

| Tool | Behavior |
| --- | --- |
| `get_available_courses()` | Active courses ordered by name and ID. |
| `get_course_details(course_id)` | Active course details or `None`. |
| `get_course_instructor(course_id)` | Active course/instructor association or `None`. |
| `get_active_classes()` | Explicitly active classes whose course is active. |
| `search_courses(query)` | Bounded case-insensitive substring search on active course names, max 20 results. |

All result records are plain dictionaries with string `course_id` values. Tools use short-lived sessions and omit student personal information. A course-name question resolves an ID only after a unique search result.

## Schema and Seed Lifecycle

`backend/database/schema.sql` is the PostgreSQL reference schema. Railway's `scripts/initialize_database.py` bootstrap applies it only when none of the five app tables exist, does nothing when all are present, and refuses a partial schema. It is not a migration tool; future schema changes require reviewed migrations. Do not use `Base.metadata.create_all()` in production.

`python -m backend.database.seed` is for local/test databases only. It creates ORM tables and merges deterministic synthetic fixtures; never run it against production. Fixtures are not actual Torilo Academy offerings, staff, schedules, or students.

## Tests

`tests/test_group3_contracts.py` uses isolated SQLite/`StaticPool` to verify seed idempotency, tools, chat delegation, request validation, health and course endpoints. PostgreSQL-specific schema/production migrations require a separately isolated PostgreSQL test database.