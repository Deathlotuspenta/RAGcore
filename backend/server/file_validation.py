"""上传文件类型与内容校验：仅允许文档，拒绝图片等二进制。"""

from pathlib import Path

from fastapi import HTTPException, status

from server import config

# 允许导入的扩展名
ALLOWED_EXTENSIONS = frozenset({"md", "markdown", "txt", "pdf"})

# 明确拒绝（即使误改扩展名也会用魔数再拦一层）
BLOCKED_EXTENSIONS = frozenset({
    "jpg", "jpeg", "png", "gif", "webp", "bmp", "svg", "ico", "heic", "heif",
    "tiff", "tif", "avif",
    "mp4", "avi", "mov", "mkv", "wmv", "flv", "webm",
    "mp3", "wav", "flac", "aac", "ogg",
    "zip", "rar", "7z", "tar", "gz", "bz2",
    "exe", "dll", "so", "dylib", "dmg", "apk", "ipa",
    "doc", "docx", "xls", "xlsx", "ppt", "pptx",  # 后续可扩展
})

# 常见文件魔数（用于识别伪装扩展名）
_IMAGE_SIGNATURES = (
    b"\x89PNG\r\n\x1a\n",
    b"\xff\xd8\xff",
    b"GIF87a",
    b"GIF89a",
    b"BM",
    b"II*\x00",
    b"MM\x00*",
)
_PDF_SIGNATURE = b"%PDF"


def extension_of(filename: str) -> str:
    return Path(filename or "").suffix.lstrip(".").lower()


def validate_upload(filename: str, data: bytes) -> str:
    """
    校验上传文件，返回规范化 file_type（md / txt / pdf）。
    不通过则抛出 HTTPException。
    """
    if not filename:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "缺少文件名")

    ext = extension_of(filename)
    if not ext:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "文件缺少扩展名")

    if ext in BLOCKED_EXTENSIONS:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"不支持该文件类型（.{ext}），请勿上传图片、音视频或压缩包",
        )

    if ext not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(f".{e}" for e in sorted(ALLOWED_EXTENSIONS))
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"仅支持导入：{allowed}",
        )

    max_bytes = config.MAX_UPLOAD_BYTES
    if len(data) > max_bytes:
        mb = config.MAX_UPLOAD_MB
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            f"文件过大，最大 {mb} MB",
        )

    if len(data) == 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "文件为空")

    _reject_known_binary(data)

    if ext == "pdf":
        if not data.lstrip()[:4].startswith(b"%PDF"):
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "不是有效的 PDF 文件"
            )
        return "pdf"

    # md / markdown / txt：必须是可读文本
    if not _is_text_content(data):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "文件内容不是有效文本，疑似二进制或图片，无法导入",
        )

    return "md" if ext in {"md", "markdown"} else "txt"


def _reject_known_binary(data: bytes) -> None:
    head = data[:16]
    for sig in _IMAGE_SIGNATURES:
        if head.startswith(sig):
            raise HTTPException(
                status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                "不支持图片文件",
            )
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            "不支持 WebP 图片",
        )


def _is_text_content(data: bytes) -> bool:
    sample = data[:8192]
    if b"\x00" in sample:
        return False
    for encoding in ("utf-8", "gb18030", "latin-1"):
        try:
            data.decode(encoding)
            return True
        except UnicodeDecodeError:
            continue
    return False


def supported_formats_message() -> str:
    return "支持批量导入：.md、.markdown、.txt、.pdf"
