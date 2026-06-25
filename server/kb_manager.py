# [总览] 入库 = chunk → embed → Chroma(每块) + SQLite(每篇)
# 学习文档：studydocuments/kb_manager入库学习指南.md

import sqlite3  # [学习点1] Python 标准库：轻量 SQL 数据库
import uuid  # [学习点3] 生成 note_id，保证全局唯一
from datetime import datetime, timezone  # [学习点9] 记录上传时间（UTC ISO 格式）
from pathlib import Path  # [学习点5] 创建 storage 目录

import chromadb  # [学习点1][学习点6] 向量库，pip install chromadb
import hashlib
from server import config  # [学习点1] 读取 .env 中的路径配置
from server.chunker import chunk  # [学习点4] 语义切块
from server.embedding_local import embed_text  # [学习点4] 批量向量化



def add_note(title, content, file_type):
    """把一篇笔记存进去，返回 note_id"""
    content = content.strip()
    if not content:
        return {"code": 2, "message": "内容不能为空"}


    Path(config.CHROMA_PERSIST_DIR).mkdir(parents=True, exist_ok=True)
    # 创建表
    conn = sqlite3.connect(config.DB_PATH)
    create_table_sql = conn.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id TEXT PRIMARY KEY,
            title TEXT,
            file_type TEXT,
            created_at TEXT,
            chunk_count INTEGER,
            content_hash TEXT UNIQUE NOT NULL
        )
    """).fetchone()

    # content换算hash
    content_hash = hashlib.sha256(content.encode()).hexdigest()
    # 检查是否存在sqlite中
    
    cursor = conn.execute("SELECT id FROM notes WHERE content_hash = ?", (content_hash,))
    result = cursor.fetchone()
    # 存在就跳过返回提示词已经存在
    if result:
        conn.close()
        return {"code": 1, "message": "词条已经存在","note_id": result[0]}

    note_id = str(uuid.uuid4())

    # [学习点4] RAG 入库核心两步：先切块，再 embed（顺序不能反）
    chunks:list[str] = chunk(content)
    vectors:list[list[float]] = embed_text(chunks)

    # --- [学习点5][学习点6][学习点7] 存 Chroma：每个 chunk 一条记录 ---
    
    client = chromadb.PersistentClient(path=config.CHROMA_PERSIST_DIR)
    collection = client.get_or_create_collection("notes")

    collection.add(
        # [学习点7] ids：每块唯一编号；列表推导式 + f-string
        ids=[f"{note_id}-{i}" for i in range(len(chunks))],
        documents=chunks,  # 原文，检索后要展示
        embeddings=vectors,  # 向量，检索时算相似度
        metadatas=[{"note_id": note_id, "note_title": title} for _ in chunks],
    )

    # --- [学习点8][学习点9] 存 SQLite：整篇笔记一条元数据 ---
    Path(config.DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    
    
    conn.execute(
        "INSERT INTO notes VALUES (?, ?, ?, ?, ?, ?)",  # ? 占位符防注入
        (note_id, title, file_type, datetime.now(timezone.utc).isoformat(), len(chunks), content_hash),
    )
    conn.commit()  # 提交事务，数据才真正写入磁盘
    conn.close()

    return {"code": 0, "message": "词条添加成功", "note_id": note_id}

def query_notes(query:str, top_k:int = 10):
    """查询笔记"""
    client = chromadb.PersistentClient(path=config.CHROMA_PERSIST_DIR)
    collection = client.get_or_create_collection("notes")
    results = collection.query(
        query_embeddings=embed_text([query]),
        n_results=top_k
    )
    return results

def update_note(note_id, title, content, file_type):
    # TODO 未完成后续补齐
    """更新笔记"""
    client = chromadb.PersistentClient(path=config.CHROMA_PERSIST_DIR)
    collection = client.get_or_create_collection("notes")
    collection.update(
        ids=[note_id],
        documents=[content],
    )
    return {"code": 0, "message": "词条更新成功"}

if __name__ == "__main__":
    # # [学习点10] 模块自测：python -m server.kb_manager
    # from server.parser import parse_file
    # text = parse_file("test_data/台账.md")
    # note_id = add_note("台账管理", text, "md")
    # print("成功了！note_id =", note_id)

    results = query_notes("Deepseek密钥",2)
    # print(results["documents"])
    # print("-"*100)
    for result in results["documents"][0]:
        print(result)
        print("-"*100)