from typing import Any, Literal

from pydantic import BaseModel, Field


class DocumentUploadResponse(BaseModel):
    filename: str
    pages: int
    first_page_preview: str | None
    metadata: dict[str, Any] | None


class DocumentSplitResponse(BaseModel):
    filename: str
    pages: int
    chunks: int
    first_chunk_preview: str | None
    first_chunk_metadata: dict[str, Any] | None


class TextSplitRequest(BaseModel):
    text: str = Field(min_length=1, max_length=200_000)
    chunk_size: int = Field(default=1000, ge=100, le=8000)
    chunk_overlap: int = Field(default=150, ge=0, le=2000)
    splitter_type: str = "recursive"


class TextSplitResponse(BaseModel):
    splitter_type: str
    chunk_size: int
    chunk_overlap: int
    chunks: int
    results: list[str]


class DocumentIndexResponse(BaseModel):
    filename: str
    pages: int
    chunks_indexed: int


class DocumentSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    k: int = Field(default=3, ge=1, le=20)
    search_type: Literal["similarity", "mmr"] = "similarity"
    source: str | None = None


class DocumentSearchResult(BaseModel):
    content: str
    metadata: dict[str, Any]


class DocumentSearchResponse(BaseModel):
    query: str
    search_type: str
    k: int
    results: list[DocumentSearchResult]


class DocumentAskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    k: int = Field(default=3, ge=1, le=20)
    search_type: Literal["similarity", "mmr"] = "similarity"
    source: str | None = None


class DocumentAskSource(BaseModel):
    content: str
    metadata: dict[str, Any]


class DocumentAskResponse(BaseModel):
    question: str
    answer: str
    sources: list[DocumentAskSource]


class DocumentChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    session_id: str | None = None
    k: int = Field(default=3, ge=1, le=20)
    search_type: Literal["similarity", "mmr"] = "similarity"
    source: str | None = None


class DocumentChatSource(BaseModel):
    content: str
    metadata: dict[str, Any]


class DocumentChatMessage(BaseModel):
    role: str
    content: str


class DocumentChatResponse(BaseModel):
    session_id: str
    question: str
    answer: str
    sources: list[DocumentChatSource]
    history: list[DocumentChatMessage]


class ClearChatRequest(BaseModel):
    session_id: str


class ClearChatResponse(BaseModel):
    session_id: str
    cleared: bool
