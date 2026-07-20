from pathlib import Path

from app.services.embedding_service import get_embedding_model
from langchain_chroma import Chroma
from langchain_core.documents import Document

CHROMA_DIR = Path("storage/chroma")
COLLECTION_NAME = "rag_assistant_lab"


def create_or_load_vector_store() -> Chroma:
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)

    return Chroma(
        collection_name=COLLECTION_NAME,
        persist_directory=str(CHROMA_DIR),
        embedding_function=get_embedding_model(),
    )


def index_documents(documents: list[Document]) -> int:
    vector_store = create_or_load_vector_store()
    vector_store.add_documents(documents)
    return len(documents)


def retrieve_documents(
    query: str,
    k: int = 3,
    search_type: str = "similarity",
    source: str | None = None,
) -> list[Document]:
    vector_store = create_or_load_vector_store()

    metadata_filter = {"source": source} if source else None

    if search_type == "mmr":
        return vector_store.max_marginal_relevance_search(
            query,
            k=k,
            fetch_k=max(k * 3, 10),
            filter=metadata_filter,
        )

    return vector_store.similarity_search(
        query,
        k=k,
        filter=metadata_filter,
    )
