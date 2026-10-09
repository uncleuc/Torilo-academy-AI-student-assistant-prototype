"""Bootstrap the reviewed schema only in a completely empty database."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import inspect

from backend.database.database import create_database_engine

EXPECTED_TABLES = {"classes", "courses", "enrollments", "instructors", "students"}


def _schema_statements(schema_text: str) -> list[str]:
	without_line_comments = "\n".join(
		line for line in schema_text.splitlines() if not line.lstrip().startswith("--")
	)
	return [
		statement.strip()
		for statement in without_line_comments.split(";")
		if statement.strip()
	]


def initialize_database() -> None:
	"""Apply schema.sql to an empty DB; never seed data or mutate a partial schema."""
	repository_root = Path(__file__).resolve().parents[1]
	schema_path = repository_root / "backend" / "database" / "schema.sql"
	engine = create_database_engine()
	try:
		existing_tables = set(inspect(engine).get_table_names())
		app_tables = existing_tables & EXPECTED_TABLES
		if app_tables == EXPECTED_TABLES:
			print("Database schema already present; no changes applied.")
			return
		if app_tables:
			missing = sorted(EXPECTED_TABLES - app_tables)
			raise RuntimeError(
				"Database has a partial application schema; refusing to modify it. "
				f"Missing tables: {', '.join(missing)}"
			)

		statements = _schema_statements(schema_path.read_text(encoding="utf-8"))
		with engine.begin() as connection:
			for statement in statements:
				connection.exec_driver_sql(statement)
		print("Initial database schema applied. No seed data was inserted.")
	finally:
		engine.dispose()


if __name__ == "__main__":
	initialize_database()