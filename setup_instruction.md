# Setup Instructions

## Requirements

- Python 3.11 or newer
- Node.js and npm
- PostgreSQL running locally for database setup
- A repository-root `.env` configured for a **dedicated development database**

The setup scripts install dependencies and build the frontend. When development demo mode is enabled, they also initialize the local schema and load the demo course, instructor, and class records once.

## Configure Local Demo Mode

From the repository root, create `.env` from the example if needed:

```powershell
Copy-Item .env.example .env
```

Edit `.env` and set the local PostgreSQL connection and these values:

```env
ENVIRONMENT=development
DATABASE_URL=postgresql+psycopg://<user>:<password>@localhost:5432/<development_database>
DATABASE_DATA_VERIFIED=false
DATABASE_DEMO_MODE=true
```

Use a dedicated development database. The seeder refuses to overwrite course, instructor, or class rows it does not recognize. It preserves the existing legacy sample course/class IDs and any student/enrollment rows. The deleted `students.json` and `enrollments.json` fixture files are optional and will not be recreated.

The seeded instructor names and schedules are invented demo data. They are labeled in the database and API as `synthetic_demo`; they are not actual Torilo Academy staff or a current timetable. Do not enable demo mode in production. Production setup skips seeding.

## Run Setup

Windows PowerShell:

```powershell
./scripts/setup.ps1
```

Linux, macOS, or WSL:

```sh
bash scripts/setup.sh
```

The setup command installs Python and frontend dependencies, builds the UI, then runs the guarded database seeder. The first eligible local run applies the initial schema, applies the reviewed nullable-duration migration, and inserts the demo rows. On later runs it detects the complete seed and reports that no rows were changed. If demo mode is disabled, it skips database seeding. If PostgreSQL is unavailable while demo mode is enabled, setup stops with a database error; start PostgreSQL and rerun setup.

The seeder only proceeds when `ENVIRONMENT=development`, `DATABASE_DEMO_MODE=true`, and `DATABASE_DATA_VERIFIED=false`. It refuses to run against production or verified data and refuses to overwrite unrecognized course, instructor, or class records.

## Start the Application

After setup completes:

```powershell
./scripts/start.ps1
```

Or on Linux/macOS/WSL:

```sh
bash scripts/start.sh
```

The backend defaults to `http://localhost:8000`. The frontend development server defaults to `http://localhost:5173` when run separately.

## Disable Demo Data

To prevent demo records from being exposed locally, set:

```env
DATABASE_DEMO_MODE=false
DATABASE_DATA_VERIFIED=false
```

The database rows remain in PostgreSQL, but assistant database tools and public course endpoints stay disabled unless verified production data is explicitly enabled. Deleting demo rows is a separate database operation and is not performed by setup.
