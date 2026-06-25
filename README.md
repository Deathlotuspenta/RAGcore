# RAGcore

个人笔记知识库：**前后端分离** — Vue 3 前端 + FastAPI 后端 + JWT + RAG 问答。

## 目录结构

```
notes-kb/
├── backend/              # 全部后端：API、RAG、模型、数据
│   ├── server/           # FastAPI 应用
│   ├── models/           # BGE 模型（git 忽略）
│   ├── storage/          # Chroma + SQLite（git 忽略）
│   ├── scripts/          # 运维脚本
│   ├── test_data/
│   ├── docs/
│   ├── requirements.txt
│   └── .env
└── frontend/             # Vue 3 + Vite 纯前端
    └── src/
```

## 快速开始

### 1. 后端

```bash
cd backend
cp .env.example .env
# 编辑 .env：LLM_MODEL_API_KEY、JWT_SECRET

pip install -r requirements.txt
uvicorn server.main:app --reload --port 8000
```

API 文档：http://127.0.0.1:8000/docs

### 2. 前端

```bash
cd frontend
npm install
npm run dev
```

浏览器打开：http://localhost:5173（Vite 代理 `/api` → `8000`）

### 3. 重排序模型（可选）

```bash
cd backend
./scripts/download_reranker.sh
```

## 功能

| 模块 | 说明 |
|------|------|
| 注册 / 登录 | JWT Bearer Token |
| 笔记 CRUD | Markdown 编辑，异步切块 + 向量化 |
| 文件导入 | `.md` / `.txt` / `.pdf` |
| RAG 问答 | 向量检索 + 重排序 + 流式 Markdown，引用可查看原文 |

## 部署

- 前端：`npm run build`，Nginx 托管 `frontend/dist`
- 后端：单独跑 uvicorn，配置 `CORS_ORIGINS`
- 所有运行时数据在 `backend/storage/`、`backend/models/`

数据库设计见 [backend/docs/SCHEMA.md](backend/docs/SCHEMA.md)。
