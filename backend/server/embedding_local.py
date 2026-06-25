"""本地 BGE 向量化：将文本块转为 embedding，供 ChromaDB 存储与检索。"""

from functools import lru_cache

from server import config
from server.st_embeddings import STEmbeddings

_embedding_loaded = False


def is_embedding_loaded() -> bool:
    return _embedding_loaded


@lru_cache(maxsize=1)
def _get_embeddings() -> STEmbeddings:
    global _embedding_loaded
    from sentence_transformers import SentenceTransformer

    st_model = SentenceTransformer(config.EMBEDDING_MODEL_NAME)
    _embedding_loaded = True
    return STEmbeddings(st_model)


def embed_text(text: list[str]) -> list[list[float]]:
    """批量 embed 文档 chunk（入库用）。"""
    return _get_embeddings().embed_documents(text)


def embed_query(text: str) -> list[float]:
    """Embed 检索 query（与文档向量同一模型）。"""
    return _get_embeddings().embed_query(text)


if __name__ == "__main__":
    text = ["Hello, world!", "Python"]
    embeddings = embed_text(text)
    print("向量结果:")
    print(embeddings)
