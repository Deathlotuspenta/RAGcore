"""RAG chat — retrieve top-3 user chunks, then LLM answer."""

import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from server.auth.deps import get_current_user_id
from server.schemas import ChatRequest, ChatResponse, ChatSource
from server.services import llm_service, rag_service

router = APIRouter(prefix="/api/chat", tags=["chat"])


def _build_sources(hits: list[dict]) -> list[ChatSource]:
    return [
        ChatSource(
            note_id=h["metadata"]["note_id"],
            note_title=h["metadata"].get("note_title", ""),
            chunk_index=h["metadata"].get("chunk_index", 0),
            score=h.get("score"),
            excerpt=h["document"][:200],
            content=h["document"],
        )
        for h in hits
    ]


@router.post("", response_model=ChatResponse)
def ask(body: ChatRequest, user_id: str = Depends(get_current_user_id)):
    hits = rag_service.search_chunks(user_id, body.question, top_k=3)
    messages = llm_service.build_rag_messages(body.question, hits)
    answer = llm_service.chat_completion(messages)
    return ChatResponse(answer=answer, sources=_build_sources(hits))


@router.post("/stream")
def ask_stream(body: ChatRequest, user_id: str = Depends(get_current_user_id)):
    hits = rag_service.search_chunks(user_id, body.question, top_k=3)
    messages = llm_service.build_rag_messages(body.question, hits)
    sources = _build_sources(hits)

    def event_stream():
        try:
            for chunk in llm_service.chat_completion_stream(messages):
                payload = json.dumps(
                    {"type": "token", "content": chunk}, ensure_ascii=False
                )
                yield f"data: {payload}\n\n"
            sources_payload = json.dumps(
                {
                    "type": "sources",
                    "sources": [s.model_dump() for s in sources],
                },
                ensure_ascii=False,
            )
            yield f"data: {sources_payload}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except Exception as e:
            err = json.dumps(
                {"type": "error", "message": str(e)}, ensure_ascii=False
            )
            yield f"data: {err}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
