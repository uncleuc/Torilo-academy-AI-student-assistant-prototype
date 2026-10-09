
from pydantic import BaseModel


class DocumentMetadata(BaseModel):
    document_id: str
    document_type: str
    source_type: str
    organization: str
    approved: bool
    title: str | None = None
    category: str | None = None
    original_source: str | None = None
    last_verified: str | None = None
    status: str = "Active"


class Document(BaseModel):
    content: str
    source: str
    metadata: DocumentMetadata


class DocumentChunk(BaseModel):
    content: str
    source: str
    metadata: DocumentMetadata
    chunk_index: int