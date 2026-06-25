"""Pydantic request/response models."""

from pydantic import BaseModel, EmailStr, Field


# --- Auth ---

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: str


# --- Notes ---

class NoteCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)
    file_type: str = "md"


class NoteUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = Field(default=None, min_length=1)
    file_type: str | None = None


class NoteResponse(BaseModel):
    id: str
    title: str
    content: str
    file_type: str
    chunk_count: int
    created_at: str
    updated_at: str


class NoteListItem(BaseModel):
    id: str
    title: str
    file_type: str
    chunk_count: int
    created_at: str
    updated_at: str


class ImportFormatsResponse(BaseModel):
    extensions: list[str]
    message: str


class TaskAcceptedResponse(BaseModel):
    task_id: str
    message: str
    note_id: str | None = None


class TaskItem(BaseModel):
    id: str
    type: str
    type_label: str
    status: str  # pending | running | success | failed
    title: str
    note_id: str | None = None
    message: str | None = None
    error: str | None = None
    created_at: str
    updated_at: str


# --- Chat ---

class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class ChatSource(BaseModel):
    note_id: str
    note_title: str
    chunk_index: int
    score: float | None = None
    excerpt: str
    content: str  # 完整 chunk 原文


class ChatResponse(BaseModel):
    answer: str
    sources: list[ChatSource]
