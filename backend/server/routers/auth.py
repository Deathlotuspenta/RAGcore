"""User registration and login."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status

from server.auth.security import create_access_token, hash_password, verify_password
from server.database import get_conn
from server.schemas import LoginRequest, RegisterRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest):
    user_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    password_hash = hash_password(body.password)

    with get_conn() as conn:
        exists = conn.execute(
            "SELECT id FROM users WHERE email = ?", (body.email.lower(),)
        ).fetchone()
        if exists:
            raise HTTPException(status.HTTP_409_CONFLICT, "邮箱已注册")

        conn.execute(
            "INSERT INTO users (id, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (user_id, body.email.lower(), password_hash, now),
        )

    return UserResponse(id=user_id, email=body.email.lower())


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, password_hash FROM users WHERE email = ?",
            (body.email.lower(),),
        ).fetchone()

    if not row or not verify_password(body.password, row["password_hash"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "邮箱或密码错误")

    token = create_access_token(row["id"])
    return TokenResponse(access_token=token)
