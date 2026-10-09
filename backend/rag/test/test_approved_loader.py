import json

import pytest

from backend.rag.document_loader import load_documents


def test_loader_reads_only_explicitly_approved_documents(tmp_path):
	knowledge_base = tmp_path / "knowledge_base"
	knowledge_base.mkdir()
	(knowledge_base / "approved.md").write_text("approved", encoding="utf-8")
	(knowledge_base / "unlisted.md").write_text("not approved", encoding="utf-8")
	(knowledge_base / "index.json").write_text(
		json.dumps(
			[
				{
					"document": "approved.md",
					"title": "Approved document",
					"category": "test",
					"source_type": "test",
					"approved": True,
				},
				{
					"document": "unlisted.md",
					"title": "Unapproved document",
					"category": "test",
					"source_type": "test",
					"approved": False,
				},
			]
		),
		encoding="utf-8",
	)

	loaded = load_documents(knowledge_base)

	assert [(item["source"], item["content"]) for item in loaded] == [
		("approved.md", "approved")
	]


def test_loader_rejects_missing_approval_metadata(tmp_path):
	knowledge_base = tmp_path / "knowledge_base"
	knowledge_base.mkdir()
	(knowledge_base / "index.json").write_text(
		json.dumps([{"document": "missing-approval.md", "title": "Missing", "category": "test", "source_type": "test"}]),
		encoding="utf-8",
	)

	with pytest.raises(ValueError, match="boolean 'approved'"):
		load_documents(knowledge_base)