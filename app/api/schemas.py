from pydantic import BaseModel, Field

class QueryRequest(BaseModel):
    question: str = Field(
        min_length=3,
        max_length=2000,
    )

    top_k: int = Field(
        default=5,
        ge=1,
        le=5,
    )

class SourceReference(BaseModel):
    citation: str
    source: str
    page: int
    document_id: str | None = None

class QueryMetadata(BaseModel):
    request_id: str
    retrieval_count: int
    latency_ms: float
    model: str | None = None

class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceReference]
    metadata: QueryMetadata



