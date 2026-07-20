import uuid
from pathlib import Path

from app.core.rate_limit import limiter
from app.schemas.documents import (
    ClearChatRequest,
    ClearChatResponse,
    DocumentAskRequest,
    DocumentAskResponse,
    DocumentAskSource,
    DocumentChatMessage,
    DocumentChatRequest,
    DocumentChatResponse,
    DocumentChatSource,
    DocumentIndexResponse,
    DocumentSearchRequest,
    DocumentSearchResponse,
    DocumentSearchResult,
    DocumentSplitResponse,
    DocumentUploadResponse,
    TextSplitRequest,
    TextSplitResponse,
)
from app.services.chat_memory import (
    add_message,
    clear_history,
    create_session_id,
    get_history,
)
from app.services.chat_service import answer_chat_question
from app.services.document_loader import load_pdf
from app.services.qa_service import answer_question
from app.services.text_splitter import split_documents, split_text
from app.services.vector_store import index_documents, retrieve_documents
from fastapi import APIRouter, File, HTTPException, Request, UploadFile

router = APIRouter()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_UPLOAD_SIZE = 20 * 1024 * 1024


async def _read_upload_within_limit(file: UploadFile) -> bytes:
    chunks = []
    total = 0
    chunk_size = 1024 * 1024

    while chunk := await file.read(chunk_size):
        total += len(chunk)
        if total > MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"Arquivo excede o limite de {MAX_UPLOAD_SIZE // (1024 * 1024)}MB.",
            )
        chunks.append(chunk)

    return b"".join(chunks)


def _safe_upload_path(original_filename: str) -> Path:
    suffix = Path(original_filename).suffix
    return UPLOAD_DIR / f"{uuid.uuid4().hex}{suffix}"


@router.post("/upload", response_model=DocumentUploadResponse)
@limiter.limit("10/minute")
async def upload_document(request: Request, file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Arquivo sem nome.")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Apenas arquivos PDF são aceitos nesta etapa.",
        )

    file_path = _safe_upload_path(file.filename)

    content = await _read_upload_within_limit(file)
    file_path.write_bytes(content)

    pages = load_pdf(str(file_path))

    return DocumentUploadResponse(
        filename=file.filename,
        pages=len(pages),
        first_page_preview=pages[0].page_content[:500] if pages else None,
        metadata=pages[0].metadata if pages else None,
    )


@router.post("/upload-and-split", response_model=DocumentSplitResponse)
@limiter.limit("10/minute")
async def upload_and_split_document(request: Request, file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Arquivo sem nome.")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Apenas arquivos PDF são aceitos nesta etapa.",
        )

    file_path = _safe_upload_path(file.filename)

    content = await _read_upload_within_limit(file)
    file_path.write_bytes(content)

    pages = load_pdf(str(file_path))
    chunks = split_documents(pages)

    return DocumentSplitResponse(
        filename=file.filename,
        pages=len(pages),
        chunks=len(chunks),
        first_chunk_preview=chunks[0].page_content[:500] if chunks else None,
        first_chunk_metadata=chunks[0].metadata if chunks else None,
    )


@router.post("/split-text", response_model=TextSplitResponse)
async def split_text_endpoint(payload: TextSplitRequest):
    chunks = split_text(
        text=payload.text,
        chunk_size=payload.chunk_size,
        chunk_overlap=payload.chunk_overlap,
        splitter_type=payload.splitter_type,
    )

    return TextSplitResponse(
        splitter_type=payload.splitter_type,
        chunk_size=payload.chunk_size,
        chunk_overlap=payload.chunk_overlap,
        chunks=len(chunks),
        results=chunks,
    )


@router.post("/upload-and-index", response_model=DocumentIndexResponse)
@limiter.limit("10/minute")
async def upload_and_index_document(request: Request, file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Arquivo sem nome.")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Apenas arquivos PDF são aceitos nesta etapa.",
        )

    file_path = _safe_upload_path(file.filename)

    content = await _read_upload_within_limit(file)
    file_path.write_bytes(content)

    pages = load_pdf(str(file_path))
    chunks = split_documents(
        pages,
        chunk_size=1500,
        chunk_overlap=150,
    )

    chunks_indexed = index_documents(chunks)

    return DocumentIndexResponse(
        filename=file.filename,
        pages=len(pages),
        chunks_indexed=chunks_indexed,
    )


@router.post("/search", response_model=DocumentSearchResponse)
async def search_documents(payload: DocumentSearchRequest):
    docs = retrieve_documents(
        query=payload.query,
        k=payload.k,
        search_type=payload.search_type,
        source=payload.source,
    )

    return DocumentSearchResponse(
        query=payload.query,
        search_type=payload.search_type,
        k=payload.k,
        results=[
            DocumentSearchResult(
                content=doc.page_content,
                metadata=doc.metadata,
            )
            for doc in docs
        ],
    )


@router.post("/ask", response_model=DocumentAskResponse)
@limiter.limit("20/minute")
async def ask_document(request: Request, payload: DocumentAskRequest):
    docs = retrieve_documents(
        query=payload.question,
        k=payload.k,
        search_type=payload.search_type,
        source=payload.source,
    )

    answer = answer_question(
        question=payload.question,
        documents=docs,
    )

    return DocumentAskResponse(
        question=payload.question,
        answer=answer,
        sources=[
            DocumentAskSource(
                content=doc.page_content,
                metadata=doc.metadata,
            )
            for doc in docs
        ],
    )


@router.post("/chat", response_model=DocumentChatResponse)
@limiter.limit("20/minute")
async def chat_with_document(request: Request, payload: DocumentChatRequest):
    session_id = payload.session_id or create_session_id()

    history = get_history(session_id)

    docs = retrieve_documents(
        query=payload.question,
        k=payload.k,
        search_type=payload.search_type,
        source=payload.source,
    )

    answer = answer_chat_question(
        question=payload.question,
        documents=docs,
        history=history,
    )

    add_message(session_id, "user", payload.question)
    add_message(session_id, "assistant", answer)

    updated_history = get_history(session_id)

    return DocumentChatResponse(
        session_id=session_id,
        question=payload.question,
        answer=answer,
        sources=[
            DocumentChatSource(
                content=doc.page_content,
                metadata=doc.metadata,
            )
            for doc in docs
        ],
        history=[
            DocumentChatMessage(
                role=message["role"],
                content=message["content"],
            )
            for message in updated_history
        ],
    )


@router.post("/chat/clear", response_model=ClearChatResponse)
async def clear_document_chat(payload: ClearChatRequest):
    clear_history(payload.session_id)

    return ClearChatResponse(
        session_id=payload.session_id,
        cleared=True,
    )
