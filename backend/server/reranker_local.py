"""BGE CrossEncoder reranker — reorder vector search candidates by query relevance."""

import logging
from functools import lru_cache

from sentence_transformers import CrossEncoder

from server import config

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_reranker() -> CrossEncoder:
    return CrossEncoder(config.RERANK_MODEL_NAME)


def rerank(query: str, hits: list[dict], top_k: int) -> list[dict]:
    """Score (query, document) pairs and return top_k hits with rerank scores."""
    if not hits:
        return []

    if len(hits) == 1:
        hits[0]["score"] = hits[0].get("score")
        return hits

    try:
        pairs = [(query, hit["document"]) for hit in hits]
        scores = _get_reranker().predict(pairs, show_progress_bar=False)
        for hit, score in zip(hits, scores):
            hit["score"] = round(float(score), 4)
        ranked = sorted(hits, key=lambda h: h["score"], reverse=True)
        return ranked[:top_k]
    except Exception:
        logger.exception("Rerank failed, falling back to vector order")
        return hits[:top_k]
