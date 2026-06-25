"""Background indexing tasks (chunk + embed) with SQLite-backed status."""

import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from fastapi import HTTPException, status

from server.database import get_conn
from server.services import note_service

_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="index-task")

TASK_TYPE_LABELS = {
    "create": "新建笔记",
    "update": "更新索引",
    "import": "导入文件",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row_to_task(row) -> dict:
    return {
        "id": row["id"],
        "type": row["type"],
        "type_label": TASK_TYPE_LABELS.get(row["type"], row["type"]),
        "status": row["status"],
        "title": row["title"],
        "note_id": row["note_id"],
        "message": row["message"],
        "error": row["error"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _insert_task(user_id: str, task_type: str, title: str, note_id: str | None = None) -> str:
    task_id = str(uuid.uuid4())
    now = _now()
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO tasks
               (id, user_id, type, status, title, note_id, message, error, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (task_id, user_id, task_type, "pending", title, note_id, "排队中…", None, now, now),
        )
    return task_id


def _update_task(
    task_id: str,
    *,
    status: str | None = None,
    message: str | None = None,
    note_id: str | None = None,
    error: str | None = None,
) -> None:
    fields: list[str] = ["updated_at = ?"]
    values: list = [_now()]
    if status is not None:
        fields.append("status = ?")
        values.append(status)
    if message is not None:
        fields.append("message = ?")
        values.append(message)
    if note_id is not None:
        fields.append("note_id = ?")
        values.append(note_id)
    if error is not None:
        fields.append("error = ?")
        values.append(error)
    values.append(task_id)
    with get_conn() as conn:
        conn.execute(f"UPDATE tasks SET {', '.join(fields)} WHERE id = ?", values)


def _run_create(task_id: str, user_id: str, title: str, content: str, file_type: str) -> None:
    _update_task(task_id, status="running", message="正在切块并向量化…")
    try:
        note_id = note_service.persist_create_note(user_id, title, content, file_type)
        _update_task(
            task_id,
            status="success",
            message="索引完成",
            note_id=note_id,
            error=None,
        )
    except Exception as e:
        _update_task(task_id, status="failed", message="索引失败", error=str(e))


def _run_reindex(task_id: str, user_id: str, note_id: str) -> None:
    _update_task(task_id, status="running", message="正在重新切块并向量化…")
    try:
        chunk_count = note_service.reindex_note(user_id, note_id)
        _update_task(
            task_id,
            status="success",
            message=f"索引完成（{chunk_count} 块）",
            note_id=note_id,
            error=None,
        )
    except Exception as e:
        _update_task(task_id, status="failed", message="索引失败", error=str(e))


def submit_create(user_id: str, title: str, content: str, file_type: str) -> str:
    note_service.ensure_not_duplicate(user_id, content)
    task_id = _insert_task(user_id, "create", title)
    _executor.submit(_run_create, task_id, user_id, title, content, file_type)
    return task_id


def submit_update(
    user_id: str,
    note_id: str,
    title: str | None,
    content: str | None,
    file_type: str | None,
) -> str:
    saved = note_service.save_note_content(user_id, note_id, title, content, file_type)
    task_id = _insert_task(user_id, "update", saved["title"], note_id=note_id)
    _executor.submit(_run_reindex, task_id, user_id, note_id)
    return task_id


def submit_import(
    user_id: str,
    title: str,
    content: str,
    file_type: str,
) -> str:
    note_service.ensure_not_duplicate(user_id, content)
    task_id = _insert_task(user_id, "import", title)
    _executor.submit(_run_create, task_id, user_id, title, content, file_type)
    return task_id


def list_tasks(user_id: str, limit: int = 30) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT * FROM tasks WHERE user_id = ?
               ORDER BY updated_at DESC LIMIT ?""",
            (user_id, limit),
        ).fetchall()
    return [_row_to_task(r) for r in rows]


def get_task(user_id: str, task_id: str) -> dict:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM tasks WHERE id = ? AND user_id = ?",
            (task_id, user_id),
        ).fetchone()
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "任务不存在")
    return _row_to_task(row)
