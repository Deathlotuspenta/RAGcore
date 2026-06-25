# RAGcore

个人笔记知识库 RAG 核心：解析 → 语义切块 → 本地向量化 → Chroma 检索 → LLM 问答。

## 功能

- Markdown / 文本解析与语义分块（BGE + SemanticChunker）
- 笔记入库、去重（content_hash）、向量检索
- DeepSeek 等 OpenAI 兼容 API 生成回答

## 快速开始

```bash
cp .env.example .env
# 编辑 .env，填入 LLM_MODEL_API_KEY
# 下载 embedding 模型到 ./models/bge-small-zh-v1.5

pip install -r requirements.txt

# 入库
python -c "
from server.parser import parse_file
from server.kb_manager import add_note
text = parse_file('test_data/sample.md')
print(add_note('RAG入门', text, 'md'))
"

# 问答
python -m server.llm
```

## 目录结构

```
server/
  config.py          # 环境变量
  parser.py          # 文件解析
  chunker.py         # 语义切块
  embedding_local.py # BGE 向量化
  st_embeddings.py   # LangChain 转接头
  kb_manager.py      # 入库 / 检索
  llm.py             # RAG 问答
storage/             # Chroma + SQLite（运行时生成，不提交）
models/              # 本地模型（不提交）
```

## 说明

- `.env` 与 `storage/`、`models/` 不会进入版本库
- 含密钥的本地测试笔记请勿提交（见 `.gitignore`）
