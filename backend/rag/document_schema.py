from pydantic import BaseModel

from typing import Optional


class DocumentMetadata(BaseModel):
    document_id: str
    document_type: str
    source_type: str
    organization: str
    original_source: Optional[str] = None
    last_verified: Optional[str] = None
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