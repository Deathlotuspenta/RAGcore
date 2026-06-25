# RAGcore

个人笔记知识库：Vue 3 前端 + FastAPI 后端 + JWT + 本地 BGE 向量检索 + DeepSeek RAG 问答。

## 快速开始

| 角色 | 说明 |
|------|------|
| **最终用户** | 下载桌面包，双击使用 → [packaging/用户安装说明.txt](packaging/用户安装说明.txt) |
| **维护者打发布包** | → [packaging/README.md](packaging/README.md) |
| **开发者改代码** | 见下方「本地开发」 |

## 目录结构

```
notes-kb/
├── backend/server/     # FastAPI + RAG 管线
├── frontend/           # Vue 3 前端
├── packaging/          # 桌面应用构建（.app / Windows）
└── scripts/            # 开发者本地一键启动
```

## 本地开发

```bash
# 后端
cd backend
cp .env.example .env
pip install -r requirements.txt
uvicorn server.main:app --reload --port 8000

# 前端（另开终端）
cd frontend
npm install && npm run dev
# http://localhost:5173
```

或配置好 `backend/.venv` 后：

```bash
scripts/start-mac.command    # Mac
scripts/start-win.bat        # Windows
```

- API 文档：http://127.0.0.1:8000/docs
- `/health` 秒级可用；首次 RAG 才加载 embedding 模型
- 缺 reranker：`backend/scripts/download_reranker.sh`

## 功能

| 模块 | 说明 |
|------|------|
| 注册 / 登录 | JWT |
| 笔记 CRUD | Markdown，异步切块向量化 |
| 文件导入 | `.md` / `.txt` / `.pdf` |
| RAG 问答 | 检索 + 重排序 + 流式回答 |
| 设置 | 网页配置 LLM 与 API Key |

## 服务器部署

前端 `npm run build` + Nginx；后端单独 uvicorn，配置 `CORS_ORIGINS`。数据在 `backend/storage/`。

数据库设计：[backend/docs/SCHEMA.md](backend/docs/SCHEMA.md)
