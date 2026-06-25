"""文件解析：读取原始文件并转为纯文本，供后续分块与向量化。"""

import re
from pathlib import Path

SUPPORTED_TYPES = {"md", "markdown", "txt"}


def parse(file_bytes: bytes, file_type: str) -> str:
    """按文件类型解析，返回纯文本。"""
    file_type = file_type.lower().lstrip(".")
    text = file_bytes.decode("utf-8")

    if file_type in {"md", "markdown"}:
        return _markdown_to_text(text)
    if file_type == "txt":
        return text.strip()
    raise ValueError(f"不支持的文件类型: {file_type}")


def parse_file(file_path: str | Path) -> str:
    """从路径读取文件并解析为纯文本。"""
    path = Path(file_path)
    file_type = path.suffix.lstrip(".")
    return parse(path.read_bytes(), file_type)


def _markdown_to_text(text: str) -> str:
    """去掉 Markdown 标记，保留可读正文（标题文字会保留）。"""
    text = re.sub(r"```[\s\S]*?```", "", text)
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*>\s?", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*[-*+]\s+\[[ xX]\]\s+", "- ", text, flags=re.MULTILINE)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"\[(.+?)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


if __name__ == "__main__":
    # 流水线验证：读文件 → 纯文本 → 切块 → 向量化（入库由 kb_manager 负责）
    from server.chunker import chunk
    from server.embedding_local import embed_text

    project_root = Path(__file__).resolve().parent.parent
    sample_path = project_root / "test_data" / "sample.md"

    text = parse_file(sample_path)
    print(f"纯文本长度: {len(text)}")

    chunks = chunk(text)
    print(f"块数: {len(chunks)}")
    for i, piece in enumerate(chunks):
        print(f"\n--- chunk {i} (len={len(piece)}) ---")
        print(piece[:120] + ("..." if len(piece) > 120 else ""))

    vectors = embed_text(chunks)
    print(f"\n向量数: {len(vectors)}, 维度: {len(vectors[0])}")
