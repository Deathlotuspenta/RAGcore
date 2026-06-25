"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from server import config
from server.database import init_db
from server.routers import auth, chat, notes, settings, tasks


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Personal Notes RAG API",
    description="JWT auth + note CRUD + user-scoped RAG chat",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(settings.router)
app.include_router(auth.router)
app.include_router(notes.router)
app.include_router(tasks.router)
app.include_router(chat.router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/health/ready")
def health_ready():
    from server.embedding_local import is_embedding_loaded
    from server.reranker_local import is_reranker_loaded

    return {
        "status": "ok",
        "models_loaded": is_embedding_loaded(),
        "reranker_loaded": is_reranker_loaded(),
    }


def _mount_frontend() -> None:
    dist = config.STATIC_DIR
    if dist.is_dir():
        app.mount("/", StaticFiles(directory=dist, html=True), name="frontend")


if config.SERVE_STATIC:
    _mount_frontend()
