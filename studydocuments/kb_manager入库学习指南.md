# kb_manager 入库代码学习指南

> 对应源码：`server/kb_manager.py` 中的 `add_note` 函数  
> 目标：看懂每一行在干什么，并知道需要补哪些 Python / RAG 知识点才能自己写出来。

---

## 一、整体在干什么（先建立地图）

入库不是「把文件丢进文件夹」，而是把一篇笔记拆成很多 **chunk**，每块带 **向量**，分别存进两个仓库：

```
content（纯文本）
    → chunk()        切成多块
    → embed_text()   每块变成向量
    → ChromaDB       存：id + 原文 + 向量 + 元数据（每块一条）
    → SQLite         存：笔记标题、时间、块数量（整篇一条）
```

| 仓库 | 文件位置 | 存什么 | 以后用来 |
|------|----------|--------|----------|
| ChromaDB | `storage/chroma/` | chunk 原文 + embedding | **语义搜索** |
| SQLite | `storage/metadata.db` | 笔记元信息 | **列表、删除、分页** |

---

## 二、源码分段 + 必学知识点

下面按 `add_note` 的执行顺序，标注 **【学习点编号】**，与 `kb_manager.py` 里注释一致。

---

### 【学习点 1】Python 模块导入与项目结构

```python
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
import chromadb
from server import config
from server.chunker import chunk
from server.embedding_local import embed_text
```

**需要掌握：**

| 知识点 | 说明 | 去哪学 |
|--------|------|--------|
| `import` 标准库 | `sqlite3`、`uuid`、`datetime` 是 Python 内置/标准库 | Python 官方教程「模块」章节 |
| 第三方库 | `chromadb` 需 `pip install chromadb` | Chroma 官方 Quick Start |
| 包内导入 | `from server.xxx import yyy` 要求从项目根 `python -m server.kb_manager` 运行 | 本项目 `studydocuments` / 之前关于 `-m` 的说明 |

**自检：** 能说出每个 import 对应文件/库里的哪一类能力。

---

### 【学习点 2】函数定义与参数

```python
def add_note(title, content, file_type):
```

**需要掌握：**

- 函数、`def`、参数、`return`
- 这里三个参数的含义：`title` 标题、`content` 纯文本（parser 输出）、`file_type` 如 `"md"`

**自检：** 能写一个接收 3 个参数并 `return` 字符串的函数。

---

### 【学习点 3】生成唯一 ID（uuid）

```python
note_id = str(uuid.uuid4())
```

**需要掌握：**

- 为什么需要 ID：Chroma 和 SQLite 都要用同一个 `note_id` 关联「一篇笔记的多块 chunk」
- `uuid.uuid4()`：随机唯一字符串，如 `"f47ac10b-58cc-4372-a567-0e02b2c3d479"`

**自检：** 在 REPL 里运行 `import uuid; print(uuid.uuid4())` 三次，观察每次不同。

---

### 【学习点 4】RAG 流水线：切块 + 向量化

```python
chunks = chunk(content)
vectors = embed_text(chunks)
```

**需要掌握：**

| 概念 | 说明 |
|------|------|
| **Chunking** | 长文不能直接 embed，要切成语义块 |
| **Embedding** | 文本 → 浮点数列表（向量），语义相近的向量距离近 |
| **批量 embed** | `embed_text` 接收 `list[str]`，返回 `list[list[float]]` |

**对应模块：** `server/chunker.py`、`server/embedding_local.py`

**自检：** 能手动调用 `chunk("一段话")` 和 `embed_text(["a","b"])` 并打印 shape/长度。

---

### 【学习点 5】Path 与目录创建

```python
Path(config.CHROMA_PERSIST_DIR).mkdir(parents=True, exist_ok=True)
```

**需要掌握：**

- `pathlib.Path`：现代路径操作
- `mkdir(parents=True, exist_ok=True)`：递归创建目录，已存在不报错
- 配置来自 `.env` → `config.CHROMA_PERSIST_DIR`

**自检：** 用 Path 创建一个 `test_dir/sub`，不报错重复运行。

---

### 【学习点 6】ChromaDB 持久化客户端

```python
client = chromadb.PersistentClient(path=config.CHROMA_PERSIST_DIR)
collection = client.get_or_create_collection("notes")
```

**需要掌握：**

| 概念 | 说明 |
|------|------|
| `PersistentClient` | 数据落盘到 `storage/chroma/`，重启不丢 |
| `collection` | 类似数据库里的一张表，名字叫 `"notes"` |
| `get_or_create_collection` | 有就用，没有就建 |

**文档：** https://docs.trychroma.com/docs/run-chroma/persistent-client

**自检：** 能写出 3 行代码：连 client → 拿 collection → 打印 collection 名。

---

### 【学习点 7】ChromaDB `collection.add`（核心）

```python
collection.add(
    ids=[f"{note_id}-{i}" for i in range(len(chunks))],
    documents=chunks,
    embeddings=vectors,
    metadatas=[{"note_id": note_id, "note_title": title} for _ in chunks],
)
```

**需要掌握：**

| 参数 | 含义 |
|------|------|
| `ids` | 每条 chunk 的唯一编号，如 `note_id-0`、`note_id-1` |
| `documents` | 原文，搜索后要展示给用户 |
| `embeddings` | 向量，搜索时用来算相似度 |
| `metadatas` | 标签，如属于哪篇笔记、标题是什么 |

**四个列表长度必须相同**，按下标一一对应。

**需要掌握：**

- **列表推导式**：`[f"{note_id}-{i}" for i in range(len(chunks))]`
- **f-string**：`f"{note_id}-{0}"`

**自检：** 给定 `chunks = ["a","b"]`，能手写出 4 个参数各 2 个元素的 `add` 调用。

---

### 【学习点 8】SQLite 连接与建表

```python
conn = sqlite3.connect(config.DB_PATH)
conn.execute("""
    CREATE TABLE IF NOT EXISTS notes (
        id TEXT PRIMARY KEY,
        title TEXT,
        file_type TEXT,
        created_at TEXT,
        chunk_count INTEGER
    )
""")
```

**需要掌握：**

| 知识点 | 说明 |
|--------|------|
| `sqlite3.connect` | 连接/创建 `.db` 文件 |
| `CREATE TABLE IF NOT EXISTS` | 表不存在才建 |
| 列类型 | `TEXT`、`INTEGER`；`PRIMARY KEY` 主键唯一 |
| 为什么用 SQLite | 管「笔记列表」，不做向量搜索 |

**自检：** 用 sqlite3 建一张只有 `id, name` 的表并插入一行。

---

### 【学习点 9】SQL 插入与占位符

```python
conn.execute(
    "INSERT INTO notes VALUES (?, ?, ?, ?, ?)",
    (note_id, title, file_type, datetime.now(timezone.utc).isoformat(), len(chunks)),
)
conn.commit()
conn.close()
```

**需要掌握：**

| 知识点 | 说明 |
|--------|------|
| `INSERT INTO ... VALUES` | 插入一行 |
| `?` 占位符 | 防 SQL 注入，值放在第二个元组里 |
| `commit()` | 提交事务，否则可能不落盘 |
| `close()` | 关闭连接 |
| `datetime.now(timezone.utc).isoformat()` | UTC 时间 ISO 字符串 |

**自检：** 插入后 `SELECT * FROM notes` 能查到（可用 DB 浏览器或 Python 查）。

---

### 【学习点 10】`if __name__ == "__main__"` 自测入口

```python
if __name__ == "__main__":
    text = parse_file("test_data/sample.md")
    note_id = add_note("RAG入门", text, "md")
    print("成功了！note_id =", note_id)
```

**需要掌握：**

- 直接运行模块时执行测试代码
- 完整链路：`parse_file` → `add_note`
- 运行命令：`python -m server.kb_manager`

**自检：** 运行后 `storage/` 下出现 `chroma/` 和 `metadata.db`。

---

## 三、知识点清单（按学习顺序）

建议按下面顺序补基础，每学完一项回去对照 `add_note` 一行行看：

| 顺序 | 主题 | 难度 | 与入库的关系 |
|------|------|------|--------------|
| 1 | Python 函数、列表、字典 | ⭐ | 整体结构 |
| 2 | f-string、列表推导式 | ⭐ | 构造 ids、metadatas |
| 3 | `pathlib.Path`、文件目录 | ⭐ | 创建 storage |
| 4 | 环境变量与 `config` | ⭐ | 路径配置 |
| 5 | RAG：chunk + embedding 概念 | ⭐⭐ | 第 19–20 行 |
| 6 | ChromaDB：`add` / `query` | ⭐⭐ | 第 22–32 行 |
| 7 | SQLite：建表、INSERT | ⭐⭐ | 第 34–51 行 |
| 8 | uuid、datetime | ⭐ | 第 16、48 行 |

---

## 四、自己重写时的步骤（不会写就按这个来）

1. **写伪代码**（中文 5 行）
2. **只写 `note_id = uuid...` + chunk + embed**，`print` 验证
3. **加 Chroma `add`**，先写 1 个 chunk 测试
4. **加 SQLite INSERT**
5. **改成多个 chunk 的列表推导式**
6. **加 `__main__` 用 sample.md 跑通**

---

## 五、常见错误

| 现象 | 原因 |
|------|------|
| `ModuleNotFoundError: chromadb` | 未安装 |
| `ids/documents/embeddings` 长度不一致 | 列表推导式写错 |
| 搜不到数据 | 查询时 collection 名或路径与入库不一致 |
| `config.DB_PATH` 为 None | `.env` 未加载或变量缺失 |
| 每次运行 duplicate id | 重复 `add_note` 且 id 相同（uuid 一般不会） |

---

## 六、学完后下一步

| 功能 | 新增知识点 |
|------|------------|
| `search_notes` | `collection.query`、`embed_query`（BGE 前缀） |
| `delete_note` | `DELETE` SQL、`collection.delete(where=...)` |
| `list_notes` | `SELECT ... LIMIT OFFSET` 分页 |
| FastAPI | 路由、`UploadFile`、依赖注入 |

---

## 七、推荐资料

- Python 官方教程：https://docs.python.org/zh-cn/3/tutorial/
- Chroma 文档：https://docs.trychroma.com/
- SQLite 教程：https://www.sqlitetutorial.net/
- 本项目：`实战计划书.md` Phase 1.6 `kb_manager.py` 章节
