"""按语义切分文档：在相邻句子语义差异较大的位置下刀，而非固定字数。"""

from functools import lru_cache

from langchain_experimental.text_splitter import SemanticChunker

from server.embedding_local import _get_embeddings


@lru_cache(maxsize=1)
def _get_splitter() -> SemanticChunker:
    return SemanticChunker(
        embeddings=_get_embeddings(),
        breakpoint_threshold_type="percentile",
        breakpoint_threshold_amount=90,
        sentence_split_regex=r"(?<=[。！？.?!])\s+",
        buffer_size=0,
    )


def chunk(text: str) -> list[str]:
    """将长文本切成语义连贯的段落列表，供后续 embed 入库。"""
    text = text.strip()
    if not text:
        return []
    return _get_splitter().split_text(text)


if __name__ == "__main__":
    text = """
    Python 是一种编程语言，适合写脚本和数据分析。
    它的语法简洁，入门比较容易。
    明天下午三点要开项目评审会，记得带进度报告。
    会议在会议室 B，老板也会参加。
    Docker 可以把应用打包成容器，部署很方便。
    生产环境一般用 docker compose 管理多个服务。
    """
    chunks = chunk(text)
    print(f"块数: {len(chunks)}")
    for i, c in enumerate(chunks):
        print(f"\n--- chunk {i} (len={len(c)}) ---")
        print(c)
