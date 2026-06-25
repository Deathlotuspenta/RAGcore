"""Note CRUD with per-user isolation and RAG indexing."""

import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException, status

from server.database import get_conn
from server.file_validation import validate_upload
from server.parser import parse
from server.services import rag_service


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _content_hash(content: str) -> str:
    return hashlib.sha256(content.strip().encode("utf-8")).hexdigest()


def _row_to_note(row) -> dict:
    return {
        "id": row["id"],
        "title": row["title"],
        "content": row["content"],
        "file_type": row["file_type"],
        "chunk_count": row["chunk_count"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _row_to_list_item(row) -> dict:
    return {
        "id": row["id"],
        "title": row["title"],
        "file_type": row["file_type"],
        "chunk_count": row["chunk_count"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def ensure_not_duplicate(user_id: str, content: str) -> None:
    content = content.strip()
    if not content:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "内容不能为空")
    h = _content_hash(content)
    with get_conn() as conn:
        dup = conn.execute(
            "SELECT id FROM notes WHERE user_id = ? AND content_hash = ?",
            (user_id, h),
        ).fetchone()
    if dup:
        raise HTTPException(status.HTTP_409_CONFLICT, "相同内容的笔记已存在")


def persist_create_note(user_id: str, title: str, content: str, file_type: str) -> str:
    """Background worker: chunk + embed + insert note. Returns note_id."""
    content = content.strip()
    if not content:
        raise ValueError("内容不能为空")

    h = _content_hash(content)
    note_id = str(uuid.uuid4())
    now = _now()

    with get_conn() as conn:
        dup = conn.execute(
            "SELECT id FROM notes WHERE user_id = ? AND content_hash = ?",
            (user_id, h),
        ).fetchone()
        if dup:
            raise ValueError("相同内容的笔记已存在")

        chunk_count = rag_service.index_note(user_id, note_id, title, content)
        conn.execute(
            """INSERT INTO notes
               (id, user_id, title, content, file_type, content_hash,
                chunk_count, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (note_id, user_id, title, content, file_type, h, chunk_count, now, now),
        )
    return note_id


def save_note_content(
    user_id: str,
    note_id: str,
    title: str | None,
    content: str | None,
    file_type: str | None,
) -> dict:
    """Save note text immediately; indexing runs in background task."""
    existing = get_note(user_id, note_id)

    new_title = title if title is not None else existing["title"]
    new_content = content.strip() if content is not None else existing["content"]
    new_file_type = file_type if file_type is not None else existing["file_type"]

    if not new_content:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "内容不能为空")

    h = _content_hash(new_content)
    now = _now()

    with get_conn() as conn:
        dup = conn.execute(
            """SELECT id FROM notes WHERE user_id = ? AND content_hash = ?
               AND id != ?""",
            (user_id, h, note_id),
        ).fetchone()
        if dup:
            raise HTTPException(status.HTTP_409_CONFLICT, "相同内容的笔记已存在")

        conn.execute(
            """UPDATE notes SET title=?, content=?, file_type=?,
               content_hash=?, updated_at=?
               WHERE id=? AND user_id=?""",
            (new_title, new_content, new_file_type, h, now, note_id, user_id),
        )

    return get_note(user_id, note_id)


def reindex_note(user_id: str, note_id: str) -> int:
    """Background worker: re-chunk and re-embed an existing note."""
    note = get_note(user_id, note_id)
    rag_service.delete_note_chunks(note_id)
    chunk_count = rag_service.index_note(
        user_id, note_id, note["title"], note["content"]
    )
    now = _now()
    with get_conn() as conn:
        conn.execute(
            "UPDATE notes SET chunk_count=?, updated_at=? WHERE id=? AND user_id=?",
            (chunk_count, now, note_id, user_id),
        )
    return chunk_count


def parse_import_file(filename: str, file_bytes: bytes, title: str | None = None) -> tuple[str, str, str]:
    """Validate and parse upload; returns (title, content, file_type)."""
    file_type = validate_upload(filename, file_bytes)
    try:
        content = parse(file_bytes, file_type)
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e)) from e
    except RuntimeError as e:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, str(e)) from e

    content = content.strip()
    if not content:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "解析后内容为空")

    note_title = (title or "").strip() or Path(filename).stem or "未命名笔记"
    return note_title, content, file_type


def list_notes(user_id: str) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT id, title, file_type, chunk_count, created_at, updated_at
               FROM notes WHERE user_id = ? ORDER BY updated_at DESC""",
            (user_id,),
        ).fetchall()
    return [_row_to_list_item(r) for r in rows]


def get_note(user_id: str, note_id: str) -> dict:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM notes WHERE id = ? AND user_id = ?",
            (note_id, user_id),
        ).fetchone()
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "笔记不存在")
    return _row_to_note(row)


def delete_note(user_id: str, note_id: str) -> None:
    get_note(user_id, note_id)
    rag_service.delete_note_chunks(note_id)
    with get_conn() as conn:
        conn.execute("DELETE FROM notes WHERE id = ? AND user_id = ?", (note_id, user_id))
