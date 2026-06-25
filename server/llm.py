import httpx
from server import config
from server.kb_manager import query_notes
def generate_response(messages: list[dict]):
    response = httpx.post(
        config.LLM_MODEL_URL,
        headers={
            "Authorization": f"Bearer {config.LLM_MODEL_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": config.LLM_MODEL_NAME,
            "messages": messages
        },
        timeout=60.0
    )
    return response.text

if __name__ == "__main__":

    messages = [
        {"role": "system", "content": "你是一个知识库助手，请根据用户问题和参考内容给出回答。也需要标记参考内容的来源。"},
       
    ]

    # 调用向量查询
    user_question = "Deepseek的密钥是什么？"
    results = query_notes(user_question,2)

    # print(results)
    rag_context = ""

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    for document, metadata in zip(documents, metadatas):
        title = metadata["note_title"]
        content = document
        rag_context += f"笔记标题：{title}\n参考内容：{content}\n来源：{title}\n"

    messages.append({"role": "user", "content": f"参考内容：{rag_context} \n 如果没有参考答案就使用你原有的知识回答，用户问题：{user_question}"})
    
    # 调用LLM生成响应
    response = generate_response(messages)
    print(response)