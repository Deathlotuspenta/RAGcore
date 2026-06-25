"""Vector indexing and user-scoped retrieval."""

from pathlib import Path

import chromadb

from server import config
from server.chunker import chunk
from server.embedding_local import embed_query, embed_text
from server.reranker_local import rerank


def _collection():
    Path(config.CHROMA_PERSIST_DIR).mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=config.CHROMA_PERSIST_DIR)
    return client.get_or_create_collection("notes")


def index_note(user_id: str, note_id: str, title: str, content: str) -> int:
    """Chunk + embed + store in Chroma. Returns chunk count."""
    chunks = chunk(content)
    if not chunks:
        return 0

    vectors = embed_text(chunks)
    collection = _collection()
    collection.add(
        ids=[f"{note_id}-{i}" for i in range(len(chunks))],
        documents=chunks,
        embeddings=vectors,
        metadatas=[
            {
                "note_id": note_id,
                "user_id": user_id,
                "note_title": title,
                "chunk_index": i,
            }
            for i in range(len(chunks))
        ],
    )
    return len(chunks)


def delete_note_chunks(note_id: str) -> None:
    """Remove all chunks for a note from Chroma."""
    collection = _collection()
    collection.delete(where={"note_id": note_id})


def search_chunks(user_id: str, query: str, top_k: int = 3) -> list[dict]:
    """
    User-scoped vector search, optionally reranked.
    Retrieves RERANK_CANDIDATES from Chroma, then CrossEncoder reranks to top_k.
    """
    collection = _collection()
    fetch_k = config.RERANK_CANDIDATES if config.RERANK_ENABLED else top_k
    fetch_k = max(fetch_k, top_k)

    results = collection.query(
        query_embeddings=[embed_query(query)],
        n_results=fetch_k,
        where={"user_id": user_id},
    )

    hits: list[dict] = []
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0] if results.get("distances") else []

    for i, (doc, meta) in enumerate(zip(documents, metadatas)):
        hit = {"document": doc, "metadata": meta}
        if i < len(distances):
            hit["vector_score"] = round(1.0 / (1.0 + distances[i]), 4)
            hit["score"] = hit["vector_score"]
        hits.append(hit)

    if config.RERANK_ENABLED and hits:
        return rerank(query, hits, top_k)
    return hits[:top_k]
