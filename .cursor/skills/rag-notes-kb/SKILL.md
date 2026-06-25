---
name: rag-notes-kb
description: >-
  Develop the notes-kb RAG pipeline: parse, semantic chunk, BGE embed, Chroma, DeepSeek Q&A.
  Use when working on backend/server or frontend Vue app for this monorepo.
---
# RAG Notes-KB (Monorepo)

## Layout

```
backend/          # API + RAG + models + storage（全部后端）
  server/         # FastAPI
  models/         # BGE（gitignored）
  storage/        # chroma + metadata.db（gitignored）
frontend/src/     # Vue 3 UI only
```

## Run

```bash
# terminal 1
cd backend && uvicorn server.main:app --reload --port 8000

# terminal 2
cd frontend && npm run dev
```

## API

- `POST /api/auth/register|login`
- `CRUD /api/notes` (JWT)
- `POST /api/chat` / `POST /api/chat/stream`
- `GET /api/tasks`

## Do not commit

`backend/.env`, `backend/storage/`, `backend/models/`, `台账.md`
