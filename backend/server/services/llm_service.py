"""LLM generation for RAG answers."""

import json

import httpx

from server import config


def _llm_payload(messages: list[dict], *, stream: bool = False) -> dict:
    """Build DeepSeek chat request body (V4 non-thinking by default)."""
    payload: dict = {
        "model": config.LLM_MODEL_NAME,
        "messages": messages,
    }
    if stream:
        payload["stream"] = True
    model = (config.LLM_MODEL_NAME or "").lower()
    if model.startswith("deepseek-v4"):
        payload["thinking"] = {"type": "disabled"}
    return payload


def chat_completion(messages: list[dict]) -> str:
    """Call DeepSeek (OpenAI-compatible) and return assistant text."""
    response = httpx.post(
        config.LLM_MODEL_URL,
        headers={
            "Authorization": f"Bearer {config.LLM_MODEL_API_KEY}",
            "Content-Type": "application/json",
        },
        json=_llm_payload(messages),
        timeout=60.0,
    )
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


def chat_completion_stream(messages: list[dict]):
    """Yield assistant text deltas from a streaming chat completion."""
    with httpx.stream(
        "POST",
        config.LLM_MODEL_URL,
        headers={
            "Authorization": f"Bearer {config.LLM_MODEL_API_KEY}",
            "Content-Type": "application/json",
        },
        json=_llm_payload(messages, stream=True),
        timeout=60.0,
    ) as response:
        response.raise_for_status()
        for line in response.iter_lines():
            if not line.startswith("data: "):
                continue
            payload = line[6:].strip()
            if payload == "[DONE]":
                break
            try:
                data = json.loads(payload)
            except json.JSONDecodeError:
                continue
            delta = data.get("choices", [{}])[0].get("delta", {}).get("content")
            if delta:
                yield delta


def build_rag_messages(question: str, hits: list[dict]) -> list[dict]:
    """Assemble system + user messages from retrieved chunks."""
    if hits:
        context_parts = []
        for i, hit in enumerate(hits, 1):
            meta = hit["metadata"]
            title = meta.get("note_title", "未知")
            idx = meta.get("chunk_index", 0)
            context_parts.append(
                f"【资料{i}】标题：{title}（块 {idx}）\n{hit['document']}"
            )
        context = "\n\n".join(context_parts)
        user_content = (
            f"参考资料：\n{context}\n\n"
            f"用户问题：{question}\n\n"
            "请仅根据参考资料回答；资料不足时明确说「笔记中未找到相关信息」。"
            "使用 Markdown 格式组织回答（标题、有序/无序列表、加粗、行内代码等）。"
            "回答末尾列出引用来源（笔记标题）。"
        )
    else:
        user_content = (
            f"用户问题：{question}\n\n"
            "未检索到相关笔记内容，请回复：笔记中未找到相关信息。"
        )

    return [
        {
            "role": "system",
            "content": (
                "你是个人知识库助手，回答简洁准确，不编造笔记中没有的内容。"
                "输出使用 Markdown 格式。"
            ),
        },
        {"role": "user", "content": user_content},
    ]
