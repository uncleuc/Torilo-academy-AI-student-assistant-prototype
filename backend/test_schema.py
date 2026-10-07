from rag.document_schema import (
    DocumentMetadata,
    Document,
    DocumentChunk,
)


metadata = DocumentMetadata(
    document_id="policy_refund",
    document_type="Refund Policy",
    source_type="Official Enrollment Agreement",
    organization="Torilo Academy",
    original_source="Master Enrollment Agreement",
    last_verified="October 2026",
    status="Active",
)


document = Document(
    content="This is a test document.",
    source="policies/refund_policy.md",
    metadata=metadata,
)


chunk = DocumentChunk(
    content="Approved refunds are processed within the applicable timeframe.",
    source=document.source,
    metadata=document.metadata,
    chunk_index=0,
)


print("METADATA")
print(metadata)

print("\nDOCUMENT")
print(document)

print("\nCHUNK")
print(chunk)