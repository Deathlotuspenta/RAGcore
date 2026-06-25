"""Note CRUD — all routes require JWT; scoped by user_id."""

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from server.auth.deps import get_current_user_id
from server.file_validation import supported_formats_message
from server.schemas import (
    BatchImportItem,
    BatchImportResponse,
    ImportFormatsResponse,
    NoteCreate,
    NoteListItem,
    NoteResponse,
    NoteUpdate,
    TaskAcceptedResponse,
)
from server.services import note_service, task_service

router = APIRouter(prefix="/api/notes", tags=["notes"])


@router.get("/import/formats", response_model=ImportFormatsResponse)
def import_formats():
    return ImportFormatsResponse(
        extensions=["md", "markdown", "txt", "pdf"],
        message=supported_formats_message(),
    )


@router.post("/upload", response_model=TaskAcceptedResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_note(
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    user_id: str = Depends(get_current_user_id),
):
    data = await file.read()
    note_title, content, file_type = note_service.parse_import_file(
        file.filename or "", data, title=title
    )
    task_id = task_service.submit_import(user_id, note_title, content, file_type)
    return TaskAcceptedResponse(
        task_id=task_id,
        message="文件已提交，正在后台建立索引",
    )


@router.post("/upload/batch", response_model=BatchImportResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_notes_batch(
    files: list[UploadFile] = File(...),
    user_id: str = Depends(get_current_user_id),
):
    if not files:
        return BatchImportResponse(items=[], message="未选择文件")
    if len(files) > 50:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "单次最多导入 50 个文件")

    items: list[BatchImportItem] = []
    ok = 0
    for f in files:
        name = f.filename or "未命名"
        try:
            data = await f.read()
            note_title, content, file_type = note_service.parse_import_file(name, data)
            task_id = task_service.submit_import(user_id, note_title, content, file_type)
            items.append(BatchImportItem(filename=name, task_id=task_id))
            ok += 1
        except Exception as e:
            detail = getattr(e, "detail", None) or str(e)
            items.append(BatchImportItem(filename=name, error=str(detail)))

    return BatchImportResponse(
        items=items,
        message=f"已提交 {ok}/{len(files)} 个文件",
    )


@router.post("", response_model=TaskAcceptedResponse, status_code=status.HTTP_202_ACCEPTED)
def create_note(body: NoteCreate, user_id: str = Depends(get_current_user_id)):
    task_id = task_service.submit_create(
        user_id, body.title, body.content, body.file_type
    )
    return TaskAcceptedResponse(
        task_id=task_id,
        message="笔记已提交，正在后台建立索引",
    )


@router.get("", response_model=list[NoteListItem])
def list_notes(user_id: str = Depends(get_current_user_id)):
    return note_service.list_notes(user_id)


@router.get("/{note_id}", response_model=NoteResponse)
def get_note(note_id: str, user_id: str = Depends(get_current_user_id)):
    return note_service.get_note(user_id, note_id)


@router.put("/{note_id}", response_model=TaskAcceptedResponse, status_code=status.HTTP_202_ACCEPTED)
def update_note(
    note_id: str,
    body: NoteUpdate,
    user_id: str = Depends(get_current_user_id),
):
    task_id = task_service.submit_update(
        user_id, note_id, body.title, body.content, body.file_type
    )
    return TaskAcceptedResponse(
        task_id=task_id,
        message="笔记已保存，正在后台重新索引",
        note_id=note_id,
    )


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(note_id: str, user_id: str = Depends(get_current_user_id)):
    note_service.delete_note(user_id, note_id)
