"""文件解析：读取原始文件并转为纯文本，供后续分块与向量化。"""

import re
from pathlib import Path

SUPPORTED_TYPES = {"md", "markdown", "txt", "pdf"}


def parse(file_bytes: bytes, file_type: str) -> str:
    """按文件类型解析，返回纯文本。"""
    file_type = file_type.lower().lstrip(".")
    if file_type not in SUPPORTED_TYPES:
        raise ValueError(f"不支持的文件类型: {file_type}")

    if file_type == "pdf":
        return _parse_pdf(file_bytes)
    if file_type in {"md", "markdown"}:
        return _markdown_to_text(_decode_text(file_bytes))
    if file_type == "txt":
        return _decode_text(file_bytes).strip()
    raise ValueError(f"不支持的文件类型: {file_type}")


def parse_file(file_path: str | Path) -> str:
    """从路径读取文件并解析为纯文本。"""
    path = Path(file_path)
    file_type = path.suffix.lstrip(".")
    return parse(path.read_bytes(), file_type)


def _decode_text(data: bytes) -> str:
    for encoding in ("utf-8", "gb18030", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("无法解码文本文件")


def _parse_pdf(data: bytes) -> str:
    try:
        import fitz  # PyMuPDF
    except ImportError as e:
        raise RuntimeError("PDF 解析需要安装 pymupdf：pip install pymupdf") from e

    doc = fitz.open(stream=data, filetype="pdf")
    pages: list[str] = []
    for page in doc:
        text = page.get_text().strip()
        if text:
            pages.append(text)
    doc.close()

    if not pages:
        raise ValueError("PDF 中未提取到文字（可能是扫描件或纯图片 PDF）")

    return "\n\n".join(pages).strip()


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
