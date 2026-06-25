"""本地 BGE 向量化：将文本块转为 embedding，供 ChromaDB 存储与检索。"""

from sentence_transformers import SentenceTransformer
from server import config
from server.st_embeddings import STEmbeddings

# 服务启动时加载一次，进程内复用（避免每次请求重新下载/加载模型）
st_model = SentenceTransformer(config.EMBEDDING_MODEL_NAME)
model = STEmbeddings(st_model)


def embed_text(text: list[str]) -> list[list[float]]:
    """批量 embed 文档 chunk（入库用）。"""
    return model.embed_documents(text)


def embed_query(text: str) -> list[float]:
    """Embed 检索 query（与文档向量同一模型）。"""
    return model.embed_query(text)



if __name__ == "__main__":
    text = ["Hello, world!", "Python"]
    embeddings = embed_text(text)
    print("向量结果:")
    print(embeddings)
