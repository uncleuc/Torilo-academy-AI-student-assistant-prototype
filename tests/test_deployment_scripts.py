from pathlib import Path

from scripts.initialize_database import _schema_statements


def test_schema_bootstrap_keeps_first_statement_after_header_comment():
	root = Path(__file__).resolve().parents[1]
	schema = (root / "backend" / "database" / "schema.sql").read_text(encoding="utf-8")
	statements = _schema_statements(schema)

	assert len(statements) == 14
	assert statements[0].startswith("CREATE TABLE instructors")
	assert statements[-1].startswith("CREATE INDEX ix_enrollments_course_status")