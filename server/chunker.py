"""按语义切分文档：在相邻句子语义差异较大的位置下刀，而非固定字数。"""

from langchain_experimental.text_splitter import SemanticChunker
from server.embedding_local import model

# SemanticChunker 流程：拆句 → 逐句 embed → 算相邻句余弦距离 → 在距离突变处切分
_splitter = SemanticChunker(
    embeddings=model,
    # percentile：取距离分布的第 N 百分位作为切分阈值
    breakpoint_threshold_type="percentile",
    # 越小切得越碎（块越多），越大越保守（块越少）；90~95 是常见起点
    breakpoint_threshold_amount=90,
    # 默认 regex 偏英文标点，中文文档需显式指定
    sentence_split_regex=r"(?<=[。！？.?!])\s+",
    # BGE 单条输入有长度上限，buffer_size=0 避免多句拼接后超长
    buffer_size=0,
)


def chunk(text: str) -> list[str]:
    """将长文本切成语义连贯的段落列表，供后续 embed 入库。"""
    text = text.strip()
    if not text:
        return []
    return _splitter.split_text(text)


if __name__ == "__main__":
    # 测试文本需包含多个不同话题，否则相邻句语义相近，只会得到 1 块
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
